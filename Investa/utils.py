import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import io
from googleapiclient.http import MediaIoBaseUpload
from firebase_admin import auth



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

def upload_video_to_drive(file_path, file_name, folder_id):
    try:
        service = build('drive', 'v3', credentials=settings.GOOGLE_CREDENTIALS)

        file_metadata = {
            'name': file_name,
            'parents': [folder_id]  # Now dynamic
        }
        media = MediaFileUpload(file_path, mimetype='video/mp4')

        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

        service.permissions().create(
            fileId=file['id'],
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        return f"https://drive.google.com/uc?id={file['id']}"

    except Exception as e:
        raise Exception(f"Google Drive upload failed: {str(e)}")


def upload_image_to_drive(file_obj, file_name, folder_id):
    """
    Uploads an image to Google Drive in the specified folder and returns a public link.
    
    Args:
        file_obj: The uploaded image file (InMemoryUploadedFile).
        file_name: Name to save the file as on Google Drive.
        folder_id: ID of the Google Drive folder to upload the image to.

    Returns:
        str: Public URL to the uploaded image.
    """
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


# تحميل credentials من settings
drive_service = build(
    'drive', 'v3', credentials=settings.GOOGLE_CREDENTIALS
)

def upload_file_to_drive(file_path, file_name):
    """
    Uploads a general file (PDF, DOCX, etc.) to Google Drive
    and returns the public URL.
    """
    try:
        file_metadata = {
            "name": file_name,
            "parents": [settings.FOLDER_ID_FOR_FILES]  # فولدر الملفات مش الفيديوهات
        }

        media = MediaFileUpload(file_path, resumable=True)
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        file_id = uploaded_file.get("id")

        drive_service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()

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
