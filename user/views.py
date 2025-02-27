from django.shortcuts import render

# Create your views here.
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import send_otp_email
from django.core.cache import cache
from firebase_admin import auth, db
from .utils import upload_profile_picture
from django.core.files.storage import default_storage


@csrf_exempt
def request_otp(request):
    """Send OTP and temporarily store user details."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")
            full_name = data.get("full_name")
            gender = data.get("gender")
            national_id = data.get("national_id")
            phone = data.get("phone")
            dob = data.get("date_of_birth")

            if not email:
                return JsonResponse({"error": "Email is required"}, status=400)

            # Send OTP
            send_otp_email(email)

            # Store user details in cache for 10 minutes
            user_data = {
                "email": email,
                "password": password,
                "full_name": full_name,
                "gender": gender,
                "national_id": national_id,
                "phone": phone,
                "date_of_birth": dob
            }
            cache.set(f"user_data_{email}", user_data, timeout=600)

            return JsonResponse({"message": "OTP sent to email"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=405)

@csrf_exempt
def verify_otp(request):
    """Verify OTP and create user after successful verification with profile picture."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    try:
        # Ensure request is multipart/form-data
        if not request.content_type.startswith("multipart/form-data"):
            return JsonResponse({"error": "Request content-type must be multipart/form-data"}, status=400)

        email = request.POST.get("email")
        otp_entered = request.POST.get("otp")

        # Check stored OTP
        stored_otp = cache.get(email)
        if not stored_otp or stored_otp != otp_entered:
            return JsonResponse({"error": "Invalid or expired OTP"}, status=400)

        cache.delete(email)  # OTP is used, delete it

        # Retrieve stored user data
        user_data = cache.get(f"user_data_{email}")
        if not user_data:
            return JsonResponse({"error": "User data expired. Please sign up again."}, status=400)

        # Handle profile picture upload
        profile_picture_url = None
        if "profile_picture" in request.FILES:
            profile_picture = request.FILES["profile_picture"]
            profile_picture_url = upload_profile_picture(profile_picture, profile_picture.name)

        # Create user in Firebase Authentication
        user = auth.create_user(
            email=user_data["email"],
            password=user_data["password"],
            display_name=user_data["full_name"]
        )

        # Save user details in Firebase Realtime Database
        users_ref = db.reference("users")
        user_info = {
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "gender": user_data["gender"],
            "national_id": user_data["national_id"],
            "phone": user_data["phone"],
            "date_of_birth": user_data["date_of_birth"]
        }

        if profile_picture_url:
            user_info["profile_picture"] = profile_picture_url

        users_ref.child(user.uid).set(user_info)

        # Clear cache
        cache.delete(f"user_data_{email}")

        return JsonResponse({"message": "Account created successfully", "uid": user.uid}, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
