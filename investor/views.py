from django.http import JsonResponse
from firebase_admin import db
import json
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from collections import Counter
from django.conf import settings
from datetime import datetime
import requests
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny



@api_view(['POST'])
def interests(request):
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
    
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from datetime import datetime
import requests
import firebase_admin
from firebase_admin import db

@api_view(['POST'])
def initiate_payment(request):
    data = request.data
    amount = int(data.get("amount", 0)) * 100  
    user_id = data.get("user_id")
    project_id = data.get("project_id")

    if not all([amount, user_id, project_id]):
        return Response({"error": "Missing fields"}, status=400)

    try:
        # Step 1: Get auth token
        token_res = requests.post("https://accept.paymob.com/api/auth/tokens", json={
            "api_key": settings.PAYMOB_API_KEY
        })
        token = token_res.json()["token"]

        # Step 2: Create order
        order_res = requests.post("https://accept.paymob.com/api/ecommerce/orders", json={
            "auth_token": token,
            "delivery_needed": False,
            "amount_cents": amount,
            "currency": "EGP",
            "items": [],
        })
        order_id = order_res.json()["id"]

        # Step 3: Get payment key
        payment_key_res = requests.post("https://accept.paymob.com/api/acceptance/payment_keys", json={
            "auth_token": token,
            "amount_cents": amount,
            "expiration": 3600,
            "order_id": order_id,
            "billing_data": {
                "apartment": "NA",
                "email": "test@example.com",
                "floor": "NA",
                "first_name": "User",
                "street": "NA",
                "building": "NA",
                "phone_number": "+20123456789",
                "shipping_method": "NA",
                "postal_code": "NA",
                "city": "Cairo",
                "country": "EG",
                "last_name": "Test",
                "state": "NA"
            },
            "currency": "EGP",
            "integration_id": settings.PAYMOB_INTEGRATION_ID
        })

        payment_token = payment_key_res.json()["token"]

        # Step 4: Iframe URL
        iframe_url = f"https://accept.paymob.com/api/acceptance/iframes/{settings.PAYMOB_IFRAME_ID}?payment_token={payment_token}"

        # Step 5: Save to Firebase
        db.reference(f"payments/{user_id}").push({
            "project_id": project_id,
            "order_id": order_id,
            "amount": amount / 100,
            "status": "pending",
            "payment_token": payment_token,
            "iframe_url": iframe_url,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        return Response({"iframe_url": iframe_url}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)



@api_view(['POST'])
@permission_classes([AllowAny])
def paymob_callback(request):
    data = request.data

    try:
        transaction_id = data.get("id")
        success = data.get("success", False)
        order_id = data.get("order", {}).get("id")

        # Update Firebase based on order_id
        ref = db.reference("payments")
        all_payments = ref.get()

        if all_payments:
            for user_id, payments in all_payments.items():
                for key, payment in payments.items():
                    if payment.get("order_id") == order_id:
                        ref.child(user_id).child(key).update({
                            "status": "paid" if success else "failed",
                            "transaction_id": transaction_id,
                            "confirmed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })

        return Response({"message": "Callback processed"}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)



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

# get other projects
'''
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

'''


@api_view(['GET'])
def get_category_percentages(request):
    # Get Firebase reference to the 'projects' table
    projects_ref = settings.FIREBASE_REALTIME_DB.child('projects')
    
    # Fetch the projects data
    projects_data = projects_ref.get()
    
    if not projects_data:
        return JsonResponse({}, status=200)
    
    # Extract categories from the data
    # Since the project doesn't have an 'id', we use the values of the project
    categories = [project.get('category') for project in projects_data.values() if project.get('category')]
    
    # Calculate the percentage of each category
    total_projects = len(categories)
    category_counts = Counter(categories)
    percentages = {cat: (count / total_projects) * 100 for cat, count in category_counts.items()}
    
    # Return the calculated percentages as JSON response
    return JsonResponse(percentages)


@api_view(['POST'])
def save_project(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))

            user_id = body.get('user_id')
            project_id = body.get('project_id')

            if not (user_id and project_id):
                return JsonResponse({'error': 'Missing fields'}, status=400)

            # حفظ الربط في Firebase Realtime Database
            ref = db.reference(f'saved_projects/{user_id}')
            saved_data = {
                'project_id': project_id,
                'saved_at': datetime.now().isoformat()
            }
            new_ref = ref.push(saved_data)

            return JsonResponse({'message': 'Project saved successfully', 'saved_id': new_ref.key}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def get_saved_projects(request, user_id):
    
    if request.method == 'GET':
        try:
            limit = int(request.GET.get('limit', 10))
            offset = int(request.GET.get('offset', 0))

            ref = db.reference(f'saved_projects/{user_id}')
            projects = ref.get()

            if projects:
                project_list = []
                for key, value in projects.items():
                    value['id'] = key
                    project_list.append(value)

                project_list.sort(key=lambda x: x['saved_at'], reverse=True)
                paginated = project_list[offset:offset+limit]

                return JsonResponse(paginated, safe=False, status=200)
            else:
                return JsonResponse({'message': 'No saved projects found'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def delete_saved_project(request, user_id, saved_id):
   
    if request.method == 'DELETE':
        try:
            ref = db.reference(f'saved_projects/{user_id}/{saved_id}')
            if ref.get():
                ref.delete()
                return JsonResponse({'message': 'Saved project deleted successfully'}, status=200)
            else:
                return JsonResponse({'error': 'Saved project not found'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@api_view(['GET'])
def total_investment(request):
    user_id = request.GET.get('user_id')
    ref = db.reference('investments')
    data = ref.get()

    total = 0
    if data:
        for key, record in data.items():
            if record.get('user_id') == user_id:
                total += float(record.get('amount_invested', 0))

    return JsonResponse({'total_investment': total})

@api_view(['GET'])
def total_current_net_profit(request):
    user_id = request.GET.get('user_id')
    ref = db.reference('investments')
    data = ref.get()

    total_profit = 0
    if data:
        for key, record in data.items():
            if record.get('user_id') == user_id:
                total_profit += float(record.get('current_profit', 0))

    return JsonResponse({'total_current_net_profit': total_profit})

@api_view(['GET'])
def investment_types(request):
    user_id = request.GET.get('user_id')
    ref = db.reference('investments')
    data = ref.get()

    types = set()
    if data:
        for key, record in data.items():
            if record.get('user_id') == user_id:
                types.add(record.get('investment_type'))

    return JsonResponse({'investment_types': list(types)})

@api_view(['GET'])
def businesses_invested_in(request):
    user_id= request.GET.get('user_id')
    ref = db.reference('investments')
    data = ref.get()

    businesses = []
    if data:
        for key, record in data.items():
            if record.get('user_id') == user_id:
                businesses.append({
                    'name': record.get('business_name'),
                    'amount': float(record.get('amount_invested', 0))
                })

    return JsonResponse({'businesses': businesses})

