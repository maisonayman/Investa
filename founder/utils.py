from django.conf import settings
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseUpload


def upload_project_picture(file_obj, file_name):
    try:
        service = build("drive", "v3", credentials=settings.GOOGLE_CREDENTIALS)
        folder_id = "1seaYwKWBfPXVJugLYuTbio0BklwhT6U7"  # Replace with your actual Google Drive folder ID

        # Convert file to bytes
        file_stream = io.BytesIO(file_obj.read())  # Read file from memory
        media = MediaIoBaseUpload(file_stream, mimetype="image/jpeg", resumable=True)

        # File metadata
        file_metadata = {
            "name": file_name,
            "parents": [folder_id]
        }

        # Upload file
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        # Return the direct viewable link
        return f"https://drive.google.com/uc?id={uploaded_file['id']}"

    except Exception as e:
        raise Exception(f"Error uploading project picture: {e}")