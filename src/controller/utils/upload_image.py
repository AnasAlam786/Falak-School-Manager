import base64
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload


from dotenv import load_dotenv
import io
import json
import os



load_dotenv()

scope = ['https://www.googleapis.com/auth/drive']

def get_credentials():

    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT")

    if not creds_json:
        raise Exception("Environment variable 'GOOGLE_SERVICE_ACCOUNT' not set.")

    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=scope)
    return creds

def upload_image(image_base64, image_name, drive_folder_id):
    
    creds = get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)
    
    image_data = base64.b64decode(image_base64)
    
    byte_stream = io.BytesIO(image_data)

    media = MediaIoBaseUpload(byte_stream, mimetype='image/jpeg')
    
    file_metadata = {
        'name': str(image_name),
        'parents': [drive_folder_id]
    }
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')

    # make the file publicly accessible
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    drive_service.permissions().create(fileId=file_id, body=permission).execute()
    return file_id


def delete_image(file_id):
    try:
        creds = get_credentials()
        drive_service = build('drive', 'v3', credentials=creds)
        drive_service.files().delete(fileId=file_id).execute()
        return True  # Indicate success
    except Exception as error:
        print(f"An error occurred: {error}")
        return False  # Indicate failure
    
def move_image(file_id, new_folder_id, rename=None, older_images_folder_id=None):

    creds = get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)

    if not older_images_folder_id:
        # Get current parent folder(s) of the file
        file = drive_service.files().get(fileId=file_id, fields='parents').execute()
        older_images_folder_id = ",".join(file.get('parents'))

    # Move the file to the new folder
    drive_service.files().update(fileId=file_id, addParents=new_folder_id, removeParents=older_images_folder_id).execute()

    # Optionally rename the file
    if rename:
        drive_service.files().update(fileId=file_id, body={'name': rename}).execute()

    return True  # Indicate success



upload_image.__module__ = "src.controller.add_student.utils.upload_image"
upload_image.__name__ = "upload_image"
upload_image.__qualname__ = "upload_image"
upload_image.__doc__ = "Uploads an image to Google Drive and returns the file ID."
upload_image.__annotations__ = {
    "image": "werkzeug.datastructures.FileStorage",
    "image_name": "str",
    "drive_folder_id": "str"
}

