This is a Flask-based API for managing audio metadata in a MongoDB database. The API allows users to upload, list, search, edit, and delete audio metadata.

## **Features**

- Upload audio metadata with artist name, track name, and file URL
- List audio metadata with pagination and sorting options
- Search audio metadata by artist name or track name
- Edit existing audio metadata
- Delete audio metadata

## **Installation**

1. Install the required dependencies:

```
pip install -r requirements.txt

```

2. Start the Flask server:

```
python main.py

```

## **API Endpoints**

### **Upload Audio Metadata**

- **URL:** `/api/audio/upload`
- **Method:** POST
- **Request Body:**
    - `artistName` (string): Name of the artist
    - `trackName` (string): Name of the track
    - `fileUrl` (string): URL of the audio file
- **Response:**
    - `success` (boolean): Indicates if the upload was successful
    - `message` (string): Success or error message
    - `data` (object): Uploaded audio metadata

### **List Audio Metadata**

- **URL:** `/api/audio/list`
- **Method:** GET
- **Query Parameters:**
    - `page` (integer): Page number for pagination (default: 1)
    - `limit` (integer): Number of items per page (default: 10)
    - `sort_by` (string): Field to sort by (default: 'created_at')
    - `order` (string): Sort order ('asc' or 'desc', default: 'desc')
- **Response:**
    - `success` (boolean): Indicates if the request was successful
    - `data` (array): List of audio metadata

### **Search Audio Metadata**

- **URL:** `/api/audio/search`
- **Method:** GET
- **Query Parameters:**
    - `artistName` (string): Artist name to search for
    - `trackName` (string): Track name to search for
    - `page` (integer): Page number for pagination (default: 1)
    - `limit` (integer): Number of items per page (default: 10)
- **Response:**
    - `success` (boolean): Indicates if the request was successful
    - `data` (array): List of matching audio metadata

### **Edit Audio Metadata**

- **URL:** `/api/audio/edit/<id>`
- **Method:** PUT
- **URL Parameters:**
    - `id` (string): ID of the audio metadata to edit
- **Request Body:**
    - `artistName` (string): Updated artist name
    - `trackName` (string): Updated track name
    - `fileUrl` (string): Updated file URL
- **Response:**
    - `success` (boolean): Indicates if the update was successful
    - `message` (string): Success or error message

### **Delete Audio Metadata**

- **URL:** `/api/audio/delete/<id>`
- **Method:** DELETE
- **URL Parameters:**
    - `id` (string): ID of the audio metadata to delete
- **Response:**
    - `success` (boolean): Indicates if the deletion was successful
    - `message` (string): Success or error message

## **Error Handling**

The API returns appropriate error messages and status codes for invalid requests or server errors.