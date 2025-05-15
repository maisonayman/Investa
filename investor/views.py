from django.http import JsonResponse
from firebase_admin import db
import json
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework.decorators import api_view
import requests
import uuid 
@api_view(['POST'])
@csrf_exempt  
def interests(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            interests = data.get('interests', [])

            if not user_id or not isinstance(interests, list):
                return JsonResponse({'error': 'Invalid data'}, status=400)

            ref = db.reference(f'user_interests/{user_id}')
            ref.set({
                'interests': interests
            })

            return JsonResponse({'status': 'success'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)


PAYMENT_GATEWAY_URL = "https://accept.paymob.com/api/acceptance/payments/pay"


@api_view(['POST'])
def process_payment(request):
    data = request.data
    user_email = data.get("email")
    amount = data.get("amount")
    currency = "EGP"


    if not user_email or not amount:
        return Response({"error": "Email and amount are required"}, status=400)

    # إنشاء ID فريد للدفع
    payment_id = str(uuid.uuid4())

    # حفظ بيانات الدفع في Firebase بحالة "pending"
    payment_ref = db.reference(f'payments/{payment_id}')
    payment_ref.set({
        "user_email": user_email,
        "amount": amount,
        "currency": currency,
        "status": "pending",
        "transaction_id": None
    })

    # إرسال البيانات إلى بوابة الدفع
    payload = {
        "email": user_email,
        "amount": float(amount),
        "currency": currency
    }
    response = requests.post(PAYMENT_GATEWAY_URL, json=payload)

    if response.status_code == 200:
        transaction_id = response.json().get("transaction_id", "")

        # تحديث حالة الدفع في Firebase إلى "completed"
        payment_ref.update({
            "status": "completed",
            "transaction_id": transaction_id
        })
        return Response({"message": "Payment successful", "transaction_id": transaction_id})
    else:
        # تحديث حالة الدفع في Firebase إلى "failed"
        payment_ref.update({"status": "failed"})
        return Response({"error": "Payment failed"}, status=400)



@api_view(['GET'])
def get_user_interest_projects(request, user_id):
    # Get user's interests
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get()
    interests = user_data.get('interests', [])

    # Get all projects
    projects_ref = db.reference('projects')
    all_projects = projects_ref.get()

    # Filter matching projects
    matching_projects = [
        project for project in all_projects.values()
        if project.get('category') in interests
    ]

    return JsonResponse(matching_projects, safe=False)


@api_view(['GET'])
def get_other_projects(request, user_id):
    # Get user's interests
    user_ref = db.reference(f'users/{user_id}')
    user_data = user_ref.get()
    interests = user_data.get('interests', [])

    # Get all projects
    projects_ref = db.reference('projects')
    all_projects = projects_ref.get()

    # Filter non-matching projects
    other_projects = [
        project for project in all_projects.values()
        if project.get('category') not in interests
    ]

    return JsonResponse(other_projects, safe=False)
