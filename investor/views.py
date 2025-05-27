from django.http import JsonResponse
from firebase_admin import db
import json
from rest_framework.response import Response
from rest_framework.decorators import api_view
from collections import Counter
from django.conf import settings
from datetime import datetime
import requests
import uuid 
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_exempt



@api_view(['POST'])
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
def submit_payment(request):
    data = request.data

    project_id = data.get('project_id')
    user_national_id = data.get('user_national_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method')
    transaction_id = data.get('transaction_id')  # optional

    if not all([project_id, user_national_id, amount, payment_method]):
        return Response({"error": "Missing required fields."}, status=400)

    payment_data = {
        "project_id": project_id,
        "user_national_id": user_national_id,
        "amount": amount,
        "payment_method": payment_method,
        "transaction_id": transaction_id or "",
        "payment_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    try:
        db.reference(f"payments").push(payment_data)
        return Response({"message": "Payment recorded successfully."}, status=201)
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
def get_saved_projects(request, national_id):
    
    if request.method == 'GET':
        try:
            limit = int(request.GET.get('limit', 10))
            offset = int(request.GET.get('offset', 0))

            ref = db.reference(f'saved_projects/{national_id}')
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
def delete_saved_project(request, national_id, saved_id):
   
    if request.method == 'DELETE':
        try:
            ref = db.reference(f'saved_projects/{national_id}/{saved_id}')
            if ref.get():
                ref.delete()
                return JsonResponse({'message': 'Saved project deleted successfully'}, status=200)
            else:
                return JsonResponse({'error': 'Saved project not found'}, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def total_investment(request):
    national_id = request.GET.get('national_id')
    ref = db.reference('investments')
    data = ref.get()

    total = 0
    if data:
        for key, record in data.items():
            if record.get('national_id') == national_id:
                total += float(record.get('amount_invested', 0))

    return JsonResponse({'total_investment': total})

@csrf_exempt
def total_current_net_profit(request):
    national_id = request.GET.get('national_id')
    ref = db.reference('investments')
    data = ref.get()

    total_profit = 0
    if data:
        for key, record in data.items():
            if record.get('national_id') == national_id:
                total_profit += float(record.get('current_profit', 0))

    return JsonResponse({'total_current_net_profit': total_profit})

@csrf_exempt
def investment_types(request):
    national_id = request.GET.get('national_id')
    ref = db.reference('investments')
    data = ref.get()

    types = set()
    if data:
        for key, record in data.items():
            if record.get('national_id') == national_id:
                types.add(record.get('investment_type'))

    return JsonResponse({'investment_types': list(types)})

@csrf_exempt
def businesses_invested_in(request):
    national_id = request.GET.get('national_id')
    ref = db.reference('investments')
    data = ref.get()

    businesses = []
    if data:
        for key, record in data.items():
            if record.get('national_id') == national_id:
                businesses.append({
                    'name': record.get('business_name'),
                    'amount': float(record.get('amount_invested', 0))
                })

    return JsonResponse({'businesses': businesses})

