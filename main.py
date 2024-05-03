from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson.objectid import ObjectId
import os
from datetime import datetime
import bcrypt

app = Flask(__name__)
CORS(app)  # Enable CORS

# MongoDB connection
client = MongoClient("mongodb://dsci551admin:2024_dsci551_groupproject@52.52.64.159:27017")
db = client["MusicalChairs"]

# Hash function
# Inputs: artist_name (str), track_name (str)
# Returns: hash_value (int)
def hash_function(artist_name, track_name):
    # get artist name
    artist_name_split = artist_name.split()
    # get artist name's initial
    artist_initial = artist_name_split[0][0] + artist_name_split[-1][0]
    # change initial into number
    artist_initial_num = ord(artist_initial[0]) + ord(artist_initial[1])
    
    # get song's name
    track_name_split = track_name.split()
    # get artist name's initial
    track_initial = track_name_split[0][0] + track_name_split[-1][0]
    # change initial into number
    track_initial_num = ord(track_initial[0]) + ord(track_initial[1])
    
    # sum initial's number
    total = artist_initial_num + track_initial_num
    
    # saperate into two path
    if total == 0:
        print("Missing author's and song's name.")
    elif total%2 == 0:
        return 0
    elif total%2 == 1:
        return 1

# Function to convert ObjectId to string
# Inputs: data (list of dictionaries)
# Returns: JSON response
def jsonify_mongo(data):
    for document in data:
        if '_id' in document:
            document['_id'] = str(document['_id'])
    return jsonify(data)

# API endpoint for adding audio metadata
# Inputs: artistName (str), trackName (str), fileUrl (str)
# Returns: JSON response with success status and message
@app.route('/api/audio/upload', methods=['POST'])
def add_audio_metadata():
    data = request.json
    artist_name = data.get('artistName', '')
    track_name = data.get('trackName', '')
    file_url = data.get('fileUrl', '')
    created_at = datetime.utcnow()

    hash_value = hash_function(artist_name, track_name)
    collection_tag = f"audio_{hash_value}"

    # Insert into a specific 'audio' collection based on hash, including file URL
    audio_data = {
        'artistName': artist_name, 
        'trackName': track_name, 
        'fileUrl': file_url,  # Adding file URL
        'collection_tag': collection_tag, 
        'created_at': created_at
    }
    try:
        # Insert the audio data into the hashed collection
        result = db[collection_tag].insert_one(audio_data)
        
        # Insert reference into metadata collection for easy retrieval
        metadata_entry = {
            'artistName': artist_name,
            'trackName': track_name,
            'fileUrl': file_url,  # Store the accessible URL
            'collection_tag': collection_tag,  # Reference to the specific collection
            'audio_id': result.inserted_id,  # Reference to the specific document ID in the hashed collection
            'created_at': created_at
        }
        db.metadata.insert_one(metadata_entry)
        
        # Prepare response data
        response_data = {
            '_id': str(result.inserted_id),  # Convert ObjectId to string
            'artistName': artist_name, 
            'trackName': track_name,
            'fileUrl': file_url,
            'created_at': created_at,
            'collection_tag': collection_tag
        }
        return jsonify({'success': True, 'message': 'Audio uploaded successfully', 'data': response_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    return jsonify({'success': False, 'message': 'Invalid file type'})

# API endpoint for listing audio metadata
# Inputs: page (int), limit (int), sort_by (str), order (str)
# Returns: JSON response with success status and data
@app.route('/api/audio/list', methods=['GET'])
def list_audio():
    page = int(request.args.get('page', 1))  # Allow clients to specify page; default to 1
    limit = int(request.args.get('limit', 10))  # Allow clients to specify limit; default to 10
    skip = (page - 1) * limit

    # Set default sorting by 'created_at' in descending order
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc').lower()

    # Determine the sort order
    sort_order = DESCENDING if order == 'desc' else ASCENDING

    # Valid fields to sort by
    valid_sort_fields = ['artistName', 'trackName', 'created_at']
    if sort_by not in valid_sort_fields:
        return jsonify({'success': False, 'message': 'Invalid sort parameter'})

    try:
        # Fetching data with specified or default sorting
        audio_metadata = list(db.metadata.find({}, {'_id': 1, 'artistName': 1, 'trackName': 1, 'fileUrl': 1, 'collection_tag': 1, 'created_at': 1})
                              .sort([(sort_by, sort_order)])
                              .skip(skip).limit(limit))
        # Convert ObjectIds to strings
        for audio in audio_metadata:
            audio['_id'] = str(audio['_id'])
        return jsonify({'success': True, 'data': audio_metadata})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# API endpoint for searching audio metadata
@app.route('/api/audio/search', methods=['GET'])
def search_audio():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))  # Allow clients to specify limit; default to 10

    artist_name = request.args.get('artistName', '')
    track_name = request.args.get('trackName', '')

    if not artist_name and not track_name:
        return jsonify({'success': False, 'message': 'Please provide an artist name or track name to search.'})

    query = {}
    if artist_name:
        query['artistName'] = {'$regex': artist_name, '$options': 'i'}  # Case-insensitive partial matching
    if track_name:
        query['trackName'] = {'$regex': track_name, '$options': 'i'}  # Case-insensitive partial matching

    skip = (page - 1) * limit
    try:
        results = list(db.metadata.find(query, {'_id': 0, 'artistName': 1, 'trackName': 1, 'fileUrl': 1})
                      .collation({'locale': 'en', 'strength': 2})
                      .skip(skip).limit(limit))
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# API endpoint for editing audio metadata
# Inputs: id (str), artistName (str), trackName (str), fileUrl (str)
# Returns: JSON response with success status and message
# Note: Only fields provided by the client will be updated
@app.route('/api/audio/edit/<id>', methods=['PUT'])
def edit_audio(id):
    data = request.json
    update_data = {}
    if 'artistName' in data:
        update_data['artistName'] = data['artistName']
    if 'trackName' in data:
        update_data['trackName'] = data['trackName']
    if 'fileUrl' in data:
        update_data['fileUrl'] = data['fileUrl']

    if not update_data:
        return jsonify({'success': False, 'message': 'No valid fields provided for update'})

    try:
        # First, update the metadata
        metadata_result = db.metadata.find_one_and_update({'_id': ObjectId(id)}, {'$set': update_data})
        if not metadata_result:
            return jsonify({'success': False, 'message': 'Metadata not found'})

        # Then, update the audio collection specified by the metadata
        audio_collection_name = metadata_result['collection_tag']
        audio_result = db[audio_collection_name].update_one({'_id': ObjectId(id)}, {'$set': update_data})

        if audio_result.modified_count:
            return jsonify({'success': True, 'message': 'Audio metadata updated successfully'})
        else:
            return jsonify({'success': True, 'message': 'No changes made or document already up to date'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# API endpoint for deleting audio metadata
# Inputs: id (str)
# Returns: JSON response with success status and message
@app.route('/api/audio/delete/<id>', methods=['DELETE'])
def delete_audio(id):
    try:
        # First, fetch the metadata to get the collection tag
        metadata = db.metadata.find_one({'_id': ObjectId(id)})
        if not metadata:
            return jsonify({'success': False, 'message': 'Metadata not found'})

        # Finally, delete the metadata entry
        metadata_delete_result = db.metadata.delete_one({'_id': ObjectId(id)})
        if metadata_delete_result.deleted_count == 0:
            return jsonify({'success': False, 'message': 'Failed to delete metadata document'})

        # Delete from the specific audio collection
        # audio_collection_name = metadata['collection_tag']
        # audio_delete_result = db[audio_collection_name].delete_one({'_id': ObjectId(id)})
        # if audio_delete_result.deleted_count == 0:
        #     return jsonify({'success': False, 'message': 'Failed to delete audio document from ' + audio_collection_name})

        return jsonify({'success': True, 'message': 'Audio metadata and file deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# User registration endpoint
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    print(data)
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400

    # Check if the username already exists
    existing_user = db.users.find_one({'username': username})
    if existing_user:
        return jsonify({'success': False, 'message': 'Username already exists'}), 400

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Create a new user document
    user = {
        'username': username,
        'password': hashed_password
    }
    db.users.insert_one(user)

    return jsonify({'success': True, 'message': 'User registered successfully'}), 201

# User login endpoint
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'}), 400

    # Find the user by username
    user = db.users.find_one({'username': username})
    if not user:
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

    # Check the password
    if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

    return jsonify({'success': True, 'message': 'Login successful'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.getenv("PORT", default=5001))