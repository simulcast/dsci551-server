from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson.objectid import ObjectId
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS

# MongoDB connection
client = MongoClient("mongodb://dsci551admin:2024_dsci551_groupproject@52.52.64.159:27017")
db = client["MusicalChairs"]

# Hash function
def hash_function(artist_name, track_name):
    artist_initial = artist_name[0].upper()  # Get the first character and uppercase
    track_initial = track_name[0].upper()  # Get the first character and uppercase
    total = ord(artist_initial) + ord(track_initial)  # Sum of ASCII values
    return total % 2  # Return remainder of division by 2 (either 0 or 1)

# Function to convert ObjectId to string
def jsonify_mongo(data):
    for document in data:
        if '_id' in document:
            document['_id'] = str(document['_id'])
    return jsonify(data)

# API endpoint for adding audio metadata
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
        query['artistName'] = {'$eq': artist_name}  # Case-insensitive matching
    if track_name:
        query['trackName'] = {'$eq': track_name}  # Case-insensitive matching

    skip = (page - 1) * limit
    try:
        results = list(db.metadata.find(query, {'_id': 0, 'artistName': 1, 'trackName': 1, 'fileUrl': 1})
                      .collation({'locale': 'en', 'strength': 2})
                      .skip(skip).limit(limit))
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# API endpoint for editing audio metadata
@app.route('/api/audio/edit/<id>', methods=['PUT'])
def edit_audio(id):
    data = request.json
    update_data = {}

    # Construct an update dictionary with only the fields provided by the client
    if 'artistName' in data:
        update_data['artistName'] = data['artistName']
    if 'trackName' in data:
        update_data['trackName'] = data['trackName']
    if 'fileUrl' in data:
        update_data['fileUrl'] = data['fileUrl']

    # Ensure that there is actually data to update
    if not update_data:
        return jsonify({'success': False, 'message': 'No valid fields provided for update'})

    try:
        result = db.metadata.update_one({'_id': ObjectId(id)}, {'$set': update_data})
        if result.modified_count:
            return jsonify({'success': True, 'message': 'Audio metadata updated successfully'})
        else:
            return jsonify({'success': True, 'message': 'No changes made or document already up to date'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# API endpoint for deleting audio metadata
@app.route('/api/audio/delete/<id>', methods=['DELETE'])
def delete_audio(id):
    try:
        metadata_delete_result = db.metadata.delete_one({'_id': ObjectId(id)})
        if metadata_delete_result.deleted_count:
            return jsonify({'success': True, 'message': 'Audio metadata deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to delete metadata document'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)  # Run the Flask app
