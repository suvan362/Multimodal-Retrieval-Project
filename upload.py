from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
import os
import time
import io
import mimetypes
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient


app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'upload')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Scopes for Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive']

def create_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

def upload_file(filename, path, folder_id, mimetype):
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaFileUpload(path, mimetype=mimetype)
    service = create_service()
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def download_and_delete_file(file_id, service):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)
    with open('response.txt', 'wb') as f:
        f.write(fh.read())
        print('response.txt downloaded')
    service.files().delete(fileId=file_id).execute()
    print('response.txt deleted')

def upload_files_in_folder(local_folder_path, drive_folder_id, service):
    for filename in os.listdir(local_folder_path):
        file_path = os.path.join(local_folder_path, filename)
        if os.path.isfile(file_path):
            # Guess the MIME type of the file if not provided
            mimetype, _ = mimetypes.guess_type(file_path)
            if mimetype is None:
                mimetype = 'application/octet-stream'  # Default MIME type
            print(f'Uploading {filename}...')
            upload_file(filename, file_path, drive_folder_id, mimetype)

def retrieve_results(search_ingredients):
    # Connect to the MongoDB server running on default port
    client = MongoClient('mongodb://localhost:27017/')

    # Select the database and collection
    db = client['recipe_database']
    collection = db['recipes']
    query = [
    {
        "$match": {
            "ingredients": {
                "$in": search_ingredients
            }
        }
    },
    {
        "$addFields": {
            "matched_ingredients": {
                "$size": {
                    "$setIntersection": ["$ingredients", search_ingredients]
                }
            }
        }
    },
    {
        "$sort": {"matched_ingredients": -1}  # -1 for descending order
    }
    ]

    # Execute the query
    cur = collection.aggregate(query)
    x=0
    result=[]
    # Print the results
    for recipe in cur:
        x+=1
        result.append(recipe)
        print(recipe)
    print(x)
    return result

    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        directory = 'C:/Users/omen hub/Documents/AIR Project/upload'
        # Iterate over each entry in the directory
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)  # Get the full path to the file
            
            # Check if it is a file
            if os.path.isfile(file_path):
                os.remove(file_path)  # Delete the file
        os.remove('C:/Users/omen hub/Documents/AIR Project/response.txt')
        # Check if the 'images' part is present in uploaded files
        if 'images' not in request.files:
            return "No images part in the upload"

        # Retrieve list of uploaded image files
        images = request.files.getlist('images')

        # Create upload directory if not exists
        if not os.path.isdir(app.config['UPLOAD_FOLDER']):
            os.mkdir(app.config['UPLOAD_FOLDER'])

        # Save each image in the designated upload folder
        for image in images:
            if image.filename:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                image.save(image_path)

        # Process ingredients
        ingredients = request.form.getlist('ingredients[]')  # Get list of ingredients from the form
        ingredients_str = ', '.join(ingredients)  # Convert list to a comma-separated string
        
        # Example: Print ingredients to console (you could replace this with any processing logic)
        print("Received ingredients:", ingredients_str)
        folder_id = '1dZpvFmywLqd7Moom7UQCN3yTPnyRnv8b'  # replace with your Google Drive folder ID
        service = create_service()
        local_folder_path = 'C:/Users/omen hub/Documents/AIR Project/upload'

        upload_files_in_folder(local_folder_path, folder_id, service)
        

        print('Monitoring for response.txt...')
        response_received = False
        while not response_received:
            # Check every 10 seconds for the response.txt
            query = f"'{folder_id}' in parents and name = 'response.txt'"
            results = service.files().list(q=query).execute()
            items = results.get('files', [])
            if items:
                download_and_delete_file(items[0]['id'], service)
                response_received = True
            else:
                time.sleep(3)

        
        # Open the file for reading
        with open('response.txt', 'r') as file:
            # Read all lines from the file and store them as a list
            my_list = file.readlines()

        # Strip newline characters from each line
        my_list = [line.strip() for line in my_list]

        # Print the list to verify
        print(my_list)
        for x in my_list:
            ingredients.append(x)
        x=retrieve_results(ingredients)
        
        return render_template('result.html',recipes=x,ingredients=ingredients)

@app.route('/thankyou')
def thank_you():
    return 'Thank you for your submission!'




if __name__ == '__main__':
    app.run(debug=True)
