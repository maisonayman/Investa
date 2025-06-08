import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import io
from googleapiclient.http import MediaIoBaseUpload
from firebase_admin import auth, db
import uuid
import os


drive_service = build(
    'drive', 'v3', credentials=settings.GOOGLE_CREDENTIALS
)

# Temporary OTP storage (use a database in production)

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))


def send_otp_email(email):
    """Send OTP and store it temporarily in cache"""
    otp = generate_otp()
    
    subject = "Your OTP for Email Verification"
    message = f"Your OTP code is {otp}. It is valid for 5 minutes."
    sender = settings.EMAIL_HOST_USER
    recipient = [email]

    send_mail(subject, message, sender, recipient)

    # Store OTP in cache for 5 minutes
    cache.set(email, otp, timeout=300)


def send_password_reset_email_custom(email):
    try:
        action_code_settings = auth.ActionCodeSettings(
            url="https://ff5d-37-19-208-83.ngrok-free.app/reset-password/",  # هنا حطي رابط الفرونت أو flutter لو mobile
            handle_code_in_app=True
        )

        link = auth.generate_password_reset_link(email, action_code_settings)

        subject = "Reset Your Password"
        message = f"Click the link below to reset your password:\n\n{link}"
        sender = "no-reply@investa812.web.app"
        recipient = [email]

        send_mail(subject, message, sender, recipient)
        return True

    except Exception as e:
        raise Exception(f"Error sending password reset email: {e}")


def upload_video_to_drive(file_path, file_name, folder_id):
    try:

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]  # Now dynamic
        }
        media = MediaFileUpload(file_path, mimetype='video/mp4')

        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        drive_service.permissions().create(
            fileId=file['id'],
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        return f"https://drive.google.com/uc?id={file['id']}"

    except Exception as e:
        raise Exception(f"Google Drive upload failed: {str(e)}")


def upload_image_to_drive(file_obj, file_name, folder_id):

  
    try:
        service = build("drive", "v3", credentials=settings.GOOGLE_CREDENTIALS)

        file_stream = io.BytesIO(file_obj.read())
        media = MediaIoBaseUpload(file_stream, mimetype="image/jpeg", resumable=True)

        file_metadata = {
            "name": file_name,
            "parents": [folder_id]
        }

        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        return f"https://drive.google.com/uc?id={uploaded_file['id']}"

    except Exception as e:
        raise Exception(f"Error uploading image to Google Drive: {e}")


def upload_file_to_drive(uploaded_file, file_name):
    """
    Accepts an uploaded file (Django InMemoryUploadedFile or TemporaryUploadedFile),
    saves it temporarily, uploads it to Google Drive, and returns the public URL.
    """
    try:
        # Save the uploaded file temporarily
        temp_filename = f"/tmp/{uuid.uuid4()}_{file_name}"
        with open(temp_filename, 'wb+') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # Prepare metadata and upload to Drive
        file_metadata = {
            "name": file_name,
            "parents": [settings.FOLDER_ID_FOR_FILES]
        }
        media = MediaFileUpload(temp_filename, resumable=True)
        uploaded_file_metadata = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        # Make file public
        file_id = uploaded_file_metadata.get("id")
        drive_service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()

        # Clean up temp file
        os.remove(temp_filename)

        return f"https://drive.google.com/uc?id={file_id}"

    except Exception as e:
        print(f"Error uploading file: {e}")
        return ""


def send_password_reset_email_custom(email):
    try:
        action_code_settings = auth.ActionCodeSettings(
            url="https://ff5d-37-19-208-83.ngrok-free.app/reset-password/",  # هنا حطي رابط الفرونت أو flutter لو mobile
            handle_code_in_app=True
        )

        link = auth.generate_password_reset_link(email, action_code_settings)

        subject = "Reset Your Password"
        message = f"Click the link below to reset your password:\n\n{link}"
        sender = "no-reply@investa812.web.app"
        recipient = [email]

        send_mail(subject, message, sender, recipient)
        return True

    except Exception as e:
        raise Exception(f"Error sending password reset email: {e}")


def get_or_create_drive_folder(folder_name, parent_folder_id):
    query = f"mimeType='application/vnd.google-apps.folder' and trashed=false and name='{folder_name}' and '{parent_folder_id}' in parents"
    results = drive_service.files().list(q=query, spaces='drive',
                                         fields='files(id, name)').execute()
    folders = results.get('files', [])

    if folders:
        # Folder exists, return the first one found
        return folders[0]['id']
    else:
        # Create new folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = drive_service.files().create(body=file_metadata,
        fields='id').execute()
        return folder.get('id')


def get_founder_projects(user_id):
    projects_ref = db.reference('projects')
    projects = projects_ref.get() or {}
    return [p for p in projects.values() if p.get('owner_id') == user_id]


def get_investments_for_projects(project_ids):
    investments_ref = db.reference('investments')
    investments = investments_ref.get() or {}
    return [inv for inv in investments.values() if inv.get('project_id') in project_ids]


def get_user_data(user_id):
    ref = db.reference(f'users/{user_id}')
    return ref.get()