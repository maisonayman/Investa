import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import send_otp_email, upload_profile_picture
from django.core.cache import cache
import firebase_admin
from firebase_admin import auth, db
from rest_framework.decorators import api_view


@api_view(['POST'])
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

            if not email or not national_id:
                return JsonResponse({"error": "Email and National ID are required"}, status=400)

            # Check if national ID already exists
            existing_user = db.reference("users").child(national_id).get()
            if existing_user:
                return JsonResponse({"error": "National ID already exists"}, status=400)

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


@api_view(['POST'])
@csrf_exempt
def verify_otp(request):
    """Verify OTP and create user after successful verification with profile picture."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=405)

    try:
        if not request.content_type.startswith("multipart/form-data"):
            return JsonResponse({"error": "Request content-type must be multipart/form-data"}, status=400)

        email = request.POST.get("email")
        otp_entered = request.POST.get("otp")

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

        # Save user details in Firebase Realtime Database using national ID
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

        users_ref.child(user_data["national_id"]).set(user_info)

        # Clear cache
        cache.delete(f"user_data_{email}")

        return JsonResponse({"message": "Account created successfully", "national_id": user_data["national_id"]}, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@api_view(['POST'])
@csrf_exempt
def personal_data_list(request):
    """Handle fetching and storing personal data in Firebase using national ID."""
    ref = db.reference("personal_data")

    if request.method == 'GET':
        data = ref.get()
        return JsonResponse(data if data else {}, status=200, safe=False)

    elif request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            national_id = body.get('national_id')

            if not national_id:
                return JsonResponse({'error': 'National ID is required'}, status=400)

            # Check if national ID already exists
            existing_data = ref.child(national_id).get()
            if existing_data:
                return JsonResponse({'error': 'National ID already exists'}, status=400)

            ref.child(national_id).set({
                'full_name': body.get('full_name', ''),
                'national_id': national_id,
                'phone_number': body.get('phone_number', ''),
                'birthdate': body.get('birthdate', '2000-01-01'),
                'governor': body.get('governor', ''),
                'postal_code': body.get('postal_code', ''),
                'address': body.get('address', ''),
                'email': body.get('email', ''),
            })

            return JsonResponse({'message': 'Record created successfully', 'national_id': national_id}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)



@api_view(['POST'])
@csrf_exempt
def personal_data_detail(request, national_id):
    """Fetch, update, or delete personal data by national ID."""
    ref = db.reference("personal_data").child(national_id)

    if request.method == 'GET':
        data = ref.get()
        if not data:
            return JsonResponse({'error': 'User not found'}, status=404)
        return JsonResponse(data, status=200)

    elif request.method == 'PUT':
        try:
            body = json.loads(request.body.decode('utf-8'))
            old_data = ref.get()
            if not old_data:
                return JsonResponse({'error': 'User not found'}, status=404)

            updated_data = {
                'full_name': body.get('full_name') or old_data.get('full_name', ''),
                'phone_number': body.get('phone_number') or old_data.get('phone_number', ''),
                'birthdate': body.get('birthdate') or old_data.get('birthdate', '2000-01-01'),
                'governor': body.get('governor') or old_data.get('governor', ''),
                'postal_code': body.get('postal_code') or old_data.get('postal_code', ''),
                'address': body.get('address') or  old_data.get('address', ''),
            }

            ref.update(updated_data)

            return JsonResponse({'message': 'Record updated successfully'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    elif request.method == 'DELETE':
        ref.delete()
        return JsonResponse({'message': 'Record deleted successfully'}, status=200)

    return JsonResponse({'error': 'Method not allowed'}, status=405)



@api_view(['POST'])
@csrf_exempt
def sign_in(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            national_id = data.get("national_id")
            password = data.get("password")

            if not national_id or not password:
                return JsonResponse({"message": "Missing national_id or password"}, status=400)

            # 🔹 Step 1: Fetch user info from Firebase Realtime Database
            users_ref = db.reference("users").get()

            if not users_ref:
                return JsonResponse({"message": "No users found"}, status=404)

            user_email = None
            for user_id, user_info in users_ref.items():
                if user_info.get("national_id") == national_id:
                    user_email = user_info.get("email")
                    break

            if not user_email:
                return JsonResponse({"message": "User not found"}, status=404)

            # 🔹 Step 2: Authenticate using Firebase Authentication
            try:
                user = auth.get_user_by_email(user_email)  # Check if user exists
                custom_token = auth.create_custom_token(user.uid).decode("utf-8")  # Generate custom token

                return JsonResponse({
                    "message": "Sign-in successful",
                    "email": user_info.get("email"),
                    "user_id": user_id
                })

            except firebase_admin.auth.UserNotFoundError:
                return JsonResponse({"message": "Invalid credentials"}, status=401)

        except Exception as e:
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Invalid request method"}, status=400)


