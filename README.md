
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'maisonayman12@gmail.com'   # Replace with your Gmail
EMAIL_HOST_PASSWORD = 'wpcz hcoz gutp dtys'  # Use an App Password for security



# firebase settings

import os
import firebase_admin
from firebase_admin import credentials, db
from google.oauth2 import service_account


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to Firebase JSON key file
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "firebase_config.json")

# Initialize Firebase Admin SDK (No need for `apiKey`, `authDomain`, etc.)
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://investa812-default-rtdb.firebaseio.com/'  # Replace with your actual Realtime DB URL
    })

# Get Firebase Realtime Database Reference
FIREBASE_REALTIME_DB = db.reference()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to your service account key file
GOOGLE_DRIVE_KEY_FILE = os.path.join(BASE_DIR, "investakey.json")

# Load credentials
GOOGLE_CREDENTIALS = service_account.Credentials.from_service_account_file(
    GOOGLE_DRIVE_KEY_FILE,
    scopes=["https://www.googleapis.com/auth/drive"]
)  

# put this in the setting.py file last thing in the end 
