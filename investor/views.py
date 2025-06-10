from django.http import JsonResponse
from firebase_admin import db
import json
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from collections import Counter
from django.conf import settings
from datetime import datetime, timedelta
import requests
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from collections import defaultdict
import firebase_admin
from firebase_admin import credentials
from rest_framework.views import APIView

# Initialize Firebase (make sure this is done only once)
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'your-firebase-database-url'
    })

@api_view(['POST'])
def interests(request):
    try:
        data = json.loads(request.body)
        #user_id = data.get('user_id')
        interests = data.get('interests', [])

        #if not user_id or not isinstance(interests, list):
           #return JsonResponse({'error': 'Invalid data'}, status=400)

        ref = db.reference(f'user_interests/')
        ref.set({
            'interests': interests
       })

        return JsonResponse({'status': 'success'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
def get_user_profile(request):
    """Get user's name and profile picture from Firebase."""
    try:
        user_id = "3SB8WbQqi9Xeq6ztKbv6ZWPGhM33"  # 🔁 Replace with your testing user ID

        users_ref = db.reference("users")
        user_data = users_ref.child(user_id).get()
        
        if not user_data:
            return JsonResponse({"error": "User not found"}, status=404)
        
        profile_pic_url = user_data.get('profile_picture', '')

        response_data = {
            "username": user_data.get('username', ''),
            "profile_picture": profile_pic_url
        }

        print("User Profile Data:", response_data)  # 👀 Print for debug
        
        return JsonResponse(response_data, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@api_view(['GET'])
def get_user_interest_projects(request):
    try:
        user_id = "3SB8WbQqi9Xeq6ztKbv6ZWPGhM33"  # 🔁 Replace with your testing user ID

        user_ref = db.reference(f'users/{user_id}')
        user_data = user_ref.get()
        interests = user_data.get('interests', [])

        print("User Interests:", interests)  # 👀

        projects_ref = db.reference('projects')
        all_projects = projects_ref.get()

        matching_projects = [
            project for project in all_projects.values()
            if project.get('projectCategory') in interests
        ]

        print(f"Matching projects for user {user_id}:", matching_projects)

        return JsonResponse(matching_projects, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
def closing_soon_projects(request):
    # 1. Fetch all projects
    projects_ref = db.reference('projects')
    projects_data = projects_ref.get() or {}

    # 2. Fetch all investments
    investments_ref = db.reference('invested_projects')
    investments = investments_ref.get() or {}

    # 3. Count unique investors by type (short_term / long_term)
    investor_counts = defaultdict(lambda: {"short_term": set(), "long_term": set()})

    for inv_id, inv in investments.items():
        project_id = inv.get('project_id')
        user_id = inv.get('user_id')
        inv_type = inv.get('investment_type')  # should be "short_term" or "long_term"

        if project_id and user_id and inv_type in ['short_term', 'long_term']:
            investor_counts[project_id][inv_type].add(user_id)

    # 4. Prepare the closing soon list
    closing_projects = []

    for project_id, project in projects_data.items():
        max_short = int(project.get('max_short_term_investors', 0))
        max_long = int(project.get('max_long_term_investors', 0))

        current_short = len(investor_counts[project_id]['short_term'])
        current_long = len(investor_counts[project_id]['long_term'])

        short_left = max_short - current_short
        long_left = max_long - current_long

        # If either is close to being full (1 or 2 spots left)
        if 0 < short_left <= 2 or 0 < long_left <= 2:
            closing_projects.append({
                "project_id": project_id,
                "title": project.get('title'),
                "short_term": {
                    "max": max_short,
                    "current": current_short,
                    "spots_left": short_left
                },
                "long_term": {
                    "max": max_long,
                    "current": current_long,
                    "spots_left": long_left
                }
            })

    return Response(closing_projects)


@api_view(['GET'])
def top_raised_projects(request):
    try:
        ref = db.reference('projects')
        projects = ref.get()

        if not projects:
            return Response({'message': 'No projects found.'}, status=status.HTTP_404_NOT_FOUND)

        # Convert dict to list of projects with their keys
        project_list = [
            {"id": key, **value} for key, value in projects.items()
            if 'amount_raised' in value
        ]

        # Sort by amount_raised descending
        sorted_projects = sorted(project_list, key=lambda x: x.get('amount_raised', 0), reverse=True)

        return Response(sorted_projects[:10], status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def trending_this_month(request):
    try:
        ref = db.reference('projects')
        projects = ref.get()

        if not projects:
            return Response({'message': 'No projects found.'}, status=status.HTTP_404_NOT_FOUND)

        now = datetime.now()
        current_month = now.month
        current_year = now.year

        trending_projects = []
        for key, proj in projects.items():
            created_at = proj.get('created_at')
            if not created_at:
                continue

            try:
                created_dt = datetime.fromisoformat(created_at)
            except ValueError:
                continue

            if created_dt.month == current_month and created_dt.year == current_year:
                trending_projects.append({
                    "id": key,
                    **proj
                })

        # Sort by views or clicks if available
        trending_projects.sort(key=lambda x: x.get('views', 0), reverse=True)

        return Response(trending_projects[:10], status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


@api_view(['POST'])
def initiate_payment(request):
    data = request.data
    amount = int(data.get("amount", 0)) * 100  
    user_id = data.get("user_id")
    project_id = data.get("project_id")
    bank = data.get("bank")
    term = data.get("term")  # "short" or "long"
    charge = data.get("charge")
    total_amount = data.get("total_amount")

    if not all([amount, user_id, project_id, bank, term, charge, total_amount]):



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
            "total_amount": total_amount,
            "charge": charge,
            "bank": bank,
            "term": term,
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

        # Reference to payments in Firebase
        ref = db.reference("payments")
        all_payments = ref.get()

        if all_payments:
            for user_id, payments in all_payments.items():
                for key, payment in payments.items():
                    if payment.get("order_id") == order_id:
                        # Update payment status
                        ref.child(user_id).child(key).update({
                            "status": "paid" if success else "failed",
                            "transaction_id": transaction_id,
                            "confirmed_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })

                        # If payment successful, add to invested_projects
                        if success:
                            project_id = payment.get("project_id")
                            invested_amount = payment.get("amount")  # stored in original currency (EGP)
                            
                            # Calculate ROI (example: 10% fixed ROI)
                            roi_percent = 10
                            roi = invested_amount * (roi_percent / 100)

                            # Add to invested_projects in Firebase
                            invested_ref = db.reference("invested_projects")
                            invested_ref.push({
                                "user_id": user_id,
                                "project_id": project_id,
                                "invested_amount": invested_amount,
                                "roi": roi,
                                "invested_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                "status": "active"
                            })

        return Response({"message": "Callback processed"}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


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
    categories = [project.get('projectCategory') for project in projects_data.values() if project.get('projectCategory')]
    
    # Calculate the percentage of each category
    total_projects = len(categories)
    category_counts = Counter(categories)
    percentages = {cat: (count / total_projects) * 100 for cat, count in category_counts.items()}
    
    # Return the calculated percentages as JSON response
    return JsonResponse(percentages)


@api_view(['GET'])
def get_dashboard_summary(request, user_id):
    invested_ref = db.reference('invested_projects')
    project_ref = db.reference('projects')
    data = invested_ref.get() or {}

    total_investment = 0
    total_profit = 0
    investment_types = set()
    project_totals = {}

    for key, record in data.items():
        if record.get('user_id') == user_id:
            amount = float(record.get('invested_amount', 0))
            profit = float(record.get('current_profit', 0))
            investment_type = record.get('investment_type', '')
            project_id = record.get('project_id', '')

            if not project_id:
                continue

            if project_id not in project_totals:
                # Get project name once
                project_data = project_ref.child(project_id).get()
                project_name = project_data.get('projectName', '') if project_data else 'Unknown Project'

                project_totals[project_id] = {
                    'name': project_name,
                    'amount': amount
                }
            else:
                project_totals[project_id]['amount'] += amount

            total_investment += amount
            total_profit += profit
            investment_types.add(investment_type)

    return Response({
        "total_investment": total_investment,
        "total_current_net_profit": total_profit,
        "investment_types": list(investment_types),
        "businesses_invested_in": list(project_totals.values())
    })


@api_view(['GET'])
def search_projects(request):
    """Search projects based on query parameters."""
    try:
        # Get search parameters
        search_query = request.GET.get('q', '').lower()  # Search term
        category = request.GET.get('category', '').lower()  # Category filter
        min_investment = request.GET.get('min_investment')  # Minimum investment amount
        max_investment = request.GET.get('max_investment')  # Maximum investment amount
        
        # Get all projects from Firebase
        projects_ref = db.reference('full_projects')
        all_projects = projects_ref.get()
        
        if not all_projects:
            return JsonResponse({"projects": []}, status=200)
        
        # Convert to list and add project IDs
        projects_list = []
        for project_id, project in all_projects.items():
            project['id'] = project_id
            projects_list.append(project)
        
        # Filter projects based on search criteria
        filtered_projects = []
        for project in projects_list:
            # Search in relevant fields
            company_name = project.get('company_name', '').lower()
            service = project.get('service', '').lower()
            brief_desc = project.get('brief_desc', '').lower()
            business_type = project.get('business_type', '').lower()
            
            # Check if project matches search query
            matches_query = (
                search_query in company_name or
                search_query in service or
                search_query in brief_desc or
                search_query in business_type
            )
            
            # Check category if specified
            matches_category = True
            if category:
                project_category = project.get('business_type', '').lower()
                matches_category = category in project_category
            
            # Check investment range if specified
            matches_investment = True
            if min_investment or max_investment:
                investment = float(project.get('required_amount_of_investment', 0))
                if min_investment and investment < float(min_investment):
                    matches_investment = False
                if max_investment and investment > float(max_investment):
                    matches_investment = False
            
            # Add project if it matches all criteria
            if matches_query and matches_category and matches_investment:
                # Create a simplified project object with only the required fields
                simplified_project = {
                    'id': project.get('id'),
                    'name': project.get('company_name'),
                    'image': project.get('image'),
                    'description': project.get('brief_desc'),
                    'investors': project.get('investors', []),
                    'amount_invested': project.get('required_amount_of_investment')
                }
                filtered_projects.append(simplified_project)
        
        return JsonResponse({
            "projects": filtered_projects,
            "total": len(filtered_projects)
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@api_view(['GET'])
def get_all_projects(request):
    """
    GET /api/projects/
    Returns a JSON object of all projects stored under the "projects" node in Firebase.
    """
    try:
        projects_ref = db.reference('projects')
        data = projects_ref.get() or {}
        # data is a dict of { project_id: { …fields… }, … }
        return Response(data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": "Failed to fetch projects", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_project_by_id(request, project_id):
    """
    GET /api/projects/<project_id>/
    Returns the single project whose Firebase key is project_id.
    """
    try:
        project_ref = db.reference(f'projects/{project_id}')
        project_data = project_ref.get()
        if project_data is None:
            return Response(
                {"error": f"Project '{project_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(project_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": "Failed to fetch project", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_user_invested_projects(request, user_id):
    """
    Get all invested projects for a given user_id, grouped by project.
    Sums the ROI and investment amount per project and includes project name and investment type.
    """
    try:
        invested_ref = db.reference('invested_projects')
        all_investments = invested_ref.get() or {}

        projects_ref = db.reference('projects')
        all_projects = projects_ref.get() or {}

        grouped_investments = {}

        for inv_id, inv_data in all_investments.items():
            if inv_data.get('user_id') != user_id:
                continue

            project_id = inv_data.get('project_id')
            roi = float(inv_data.get('roi', 0))

            if project_id not in grouped_investments:
                grouped_investments[project_id] = {
                    'project_id': project_id,
                    'project_name': all_projects.get(project_id, {}).get('projectName', 'Unknown Project'),
                    'total_roi': roi,
                    'next_roi': roi-100,
                }
            else:
                grouped_investments[project_id]['total_roi'] += roi

        if not grouped_investments:
            return JsonResponse({"message": "No investments found for this user."}, status=404)

        # Convert dict to list
        result = list(grouped_investments.values())

        return JsonResponse(result, safe=False, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['POST'])
def add_invested_project(request):
    """
    Manually add an investment to the invested_projects node
    and also under the user's investments node.
    
    Expected JSON body:
    {
        "user_id": "user123",
        "project_id": "project456",
        "invested_amount": 1000,
        "roi": 100,
        "investment_type": "short"  # or "long"
    }
    """
    try:
        data = request.data
        user_id = data.get("user_id")
        project_id = data.get("project_id")
        invested_amount = data.get("invested_amount")
        roi = data.get("roi")
        investment_type = data.get("investment_type")

        if not all([user_id, project_id, invested_amount, roi, investment_type]):
            return JsonResponse({"error": "Missing fields"}, status=400)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        investment_data = {
            "user_id": user_id,
            "project_id": project_id,
            "invested_amount": invested_amount,
            "roi": roi,
            "investment_type": investment_type,
            "invested_at": timestamp,
            "status": "active"
        }

        # Save to invested_projects
        db.reference("invested_projects").push(investment_data)

        # Save to user's node
        db.reference(f"users/{user_id}/investments").push({
            "project_id": project_id,
            "invested_amount": invested_amount,
            "roi": roi,
            "investment_type": investment_type,
            "invested_at": timestamp,
            "status": "active"
        })

        return JsonResponse({"message": "Investment added successfully"}, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
def roi_vs_saving(request):
    user_id = request.GET.get('user_id')  # Or get from auth

    # Fetch user's monthly save value from Firebase
    monthlysave_ref = db.reference(f'anonymous_profiles/{user_id}/monthlysave')
    monthlysave = monthlysave_ref.get()

    if not monthlysave:
        return Response({'error': 'Monthly save value not found'}, status=404)

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']
    saving = []
    investing = []

    current_investment = 0
    roi_percent = 0.07  # 7% monthly ROI

    for i in range(8):
        # Saving is cumulative without interest
        saving.append(monthlysave * (i + 1))

        # Investment adds monthlysave + ROI on total so far
        current_investment += monthlysave
        current_investment += current_investment * roi_percent
        investing.append(round(current_investment, 2))

    return Response({
        'months': months,
        'saving': saving,
        'investing': investing
    })


@api_view(['GET'])
def balance_history(request):
    user_id = request.GET.get('user_id')  # Or from token

    ref = db.reference(f'user_investments/{user_id}')
    investments = ref.get()

    if not investments:
        return Response({'months': [], 'amounts': []})

    month_totals = defaultdict(float)

    for item in investments.values():
        amount = float(item.get('amount', 0))
        timestamp = item.get('timestamp')  # Format: '2025-01-12'

        if timestamp:
            dt = datetime.datetime.strptime(timestamp, '%Y-%m-%d')
            month_str = dt.strftime('%b')  # 'Jan', 'Feb', etc.
            month_totals[month_str] += amount

    # Sort by month order
    month_order = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan']
    result_months = []
    result_amounts = []

    for month in month_order:
        if month in month_totals:
            result_months.append(month)
            result_amounts.append(month_totals[month])

    return Response({
        'months': result_months,
        'amounts': result_amounts
    })


@api_view(['GET'])
def user_investment_project_details(request, user_id):
    try:
        # Get user's investments
        investment_ref = db.reference(f'invested_projects/{user_id}')
        investments = investment_ref.get()

        if not investments:
            return Response({"message": "No investments found"}, status=404)

        response_data = []

        for investment_id, investment_data in investments.items():
            project_id = investment_data.get('project_id')
            if not project_id:
                continue

            # Get project details
            project_ref = db.reference(f'projects/{project_id}')
            project_data = project_ref.get()

            if not project_data:
                continue

            # Combine data
            combined = {
                "project_name": project_data.get("name"),
                "category": project_data.get("category"),
                "type": project_data.get("type"),
                "start_date": investment_data.get("start_date"),
                "end_of_cycle": project_data.get("end_of_cycle"),
                "amount_of_investment": investment_data.get("amount_of_investment"),
                "roi_expected": investment_data.get("roi_expected"),
                "expected_roi": project_data.get("expected_roi"),
                "total_return": project_data.get("total_return"),
                "success_rate": project_data.get("success_rate"),
                "reinsurance": investment_data.get("reinsurance"),
                "current_roi_rate": investment_data.get("current_roi_rate"),
                "roi_q1": investment_data.get("roi_q1"),
                "roi_q2": investment_data.get("roi_q2"),
                "current_roi": investment_data.get("current_roi"),
            }

            response_data.append(combined)

        return Response(response_data)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_reports(request, project_id):
    """
    Get all reports for a specific project
    """
    try:
        print("Project ID:", project_id)  # Debug print
        
        if not project_id:
            return Response({
                'error': 'Project ID is required',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get reports from Firebase
        reports_ref = db.reference(f'projects/{project_id}/reports')
        reports = reports_ref.get()
        print("Firebase Response:", reports)  # Debug print

        if not reports:
            return Response({
                'data': [],
                'message': 'No reports found',
                'status': 'success'
            }, status=status.HTTP_200_OK)

        # Transform the data into the required format
        formatted_reports = []
        for report_id, report_data in reports.items():
            formatted_report = {
                'id': report_id,
                'title': report_data.get('title'),
                'date': report_data.get('date'),
                'return': report_data.get('return_value'),
                'type': report_data.get('type'),
                'status': report_data.get('status'),
                'details': report_data.get('details')
            }
            formatted_reports.append(formatted_report)

        return Response({
            'data': formatted_reports,
            'message': 'Reports retrieved successfully',
            'status': 'success'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print("Error:", str(e))  # Debug print
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_report(request):
    """
    Create a new report
    """
    try:
        print("Request Data:", request.data)  # Debug print
        
        # Validate required fields
        required_fields = ['project_id', 'title', 'date', 'return_value', 'type', 'details']
        missing_fields = [field for field in required_fields if field not in request.data]
        
        if missing_fields:
            return Response({
                'error': f'Missing required fields: {", ".join(missing_fields)}',
                'status': 'error',
                'received_data': request.data
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate title
        valid_titles = ['PORTFOLIO', 'MARKET', 'RISK']
        if request.data.get('title') not in valid_titles:
            return Response({
                'error': f'Invalid title. Must be one of: {", ".join(valid_titles)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate type
        valid_types = ['QUARTERLY', 'MONTHLY']
        if request.data.get('type') not in valid_types:
            return Response({
                'error': f'Invalid type. Must be one of: {", ".join(valid_types)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        report_data = {
            'title': request.data.get('title'),
            'date': request.data.get('date'),
            'return_value': request.data.get('return_value'),
            'type': request.data.get('type'),
            'status': request.data.get('status', 'ACTIVE'),
            'details': request.data.get('details'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        print("Report Data to be saved:", report_data)  # Debug print

        # Add report to Firebase
        reports_ref = db.reference(f'projects/{request.data.get("project_id")}/reports')
        new_report = reports_ref.push(report_data)

        return Response({
            'data': {
                'id': new_report.key,
                **report_data
            },
            'message': 'Report created successfully',
            'status': 'success'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print("Error:", str(e))  # Debug print
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([AllowAny])
def update_report(request, report_id):
    """
    Update an existing report
    """
    try:
        project_id = request.data.get('project_id')
        if not project_id:
            return Response({
                'error': 'Project ID is required',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        report_ref = db.reference(f'projects/{project_id}/reports/{report_id}')
        report = report_ref.get()

        if not report:
            return Response({
                'error': 'Report not found',
                'status': 'error'
            }, status=status.HTTP_404_NOT_FOUND)

        update_data = {
            'title': request.data.get('title', report.get('title')),
            'date': request.data.get('date', report.get('date')),
            'return_value': request.data.get('return_value', report.get('return_value')),
            'type': request.data.get('type', report.get('type')),
            'status': request.data.get('status', report.get('status')),
            'details': request.data.get('details', report.get('details')),
            'updated_at': datetime.now().isoformat()
        }

        report_ref.update(update_data)

        return Response({
            'data': {
                'id': report_id,
                **update_data
            },
            'message': 'Report updated successfully',
            'status': 'success'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_report(request, report_id):
    """
    Delete a report
    """
    try:
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({
                'error': 'Project ID is required',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        report_ref = db.reference(f'projects/{project_id}/reports/{report_id}')
        report = report_ref.get()

        if not report:
            return Response({
                'error': 'Report not found',
                'status': 'error'
            }, status=status.HTTP_404_NOT_FOUND)

        report_ref.delete()
        return Response({
            'message': 'Report deleted successfully',
            'status': 'success'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_transaction_reports(request, project_id):
    """
    Get all transaction reports for a specific project
    """
    try:
        print("Project ID:", project_id)  # Debug print
        
        if not project_id:
            return Response({
                'error': 'Project ID is required',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get transaction reports from Firebase
        reports_ref = db.reference(f'projects/{project_id}/transaction_reports')
        reports = reports_ref.get()
        print("Firebase Response:", reports)  # Debug print

        if not reports:
            return Response({
                'data': [],
                'message': 'No transaction reports found',
                'status': 'success'
            }, status=status.HTTP_200_OK)

        # Transform the data into the required format
        formatted_reports = []
        for report_id, report_data in reports.items():
            formatted_report = {
                'id': report_id,
                'title': report_data.get('title'),
                'date': report_data.get('date'),
                'amount': report_data.get('amount'),
                'type': report_data.get('type'),
                'status': report_data.get('status'),
                'details': report_data.get('details')
            }
            formatted_reports.append(formatted_report)

        return Response({
            'data': formatted_reports,
            'message': 'Transaction reports retrieved successfully',
            'status': 'success'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print("Error:", str(e))  # Debug print
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateTransactionReportView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Create a new transaction report
        """
        print("Method:", request.method)  # Debug print
        print("Request Data:", request.data)  # Debug print
        
        try:
            data = request.data

            # Validate required fields
            required_fields = ['project_id', 'title', 'date', 'amount', 'type', 'details']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return Response({
                    'error': f'Missing required fields: {", ".join(missing_fields)}',
                    'status': 'error',
                    'received_data': data
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate title
            valid_titles = ['TRANSACTION_HISTORY', 'SETTLEMENT_REPORT', 'TRADING_ACTIVITY']
            if data.get('title') not in valid_titles:
                return Response({
                    'error': f'Invalid title. Must be one of: {", ".join(valid_titles)}',
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate type
            valid_types = ['DAILY', 'WEEKLY']
            if data.get('type') not in valid_types:
                return Response({
                    'error': f'Invalid type. Must be one of: {", ".join(valid_types)}',
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)

            report_data = {
                'title': data.get('title'),
                'date': data.get('date'),
                'amount': data.get('amount'),
                'type': data.get('type'),
                'status': data.get('status', 'ACTIVE'),
                'details': data.get('details'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            print("Report Data to be saved:", report_data)  # Debug print

            # Add report to Firebase
            reports_ref = db.reference(f'projects/{data.get("project_id")}/transaction_reports')
            new_report = reports_ref.push(report_data)

            return Response({
                'data': {
                    'id': new_report.key,
                    **report_data
                },
                'message': 'Transaction report created successfully',
                'status': 'success'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("Error:", str(e))  # Debug print
            return Response({
                'error': str(e),
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([AllowAny])
def update_transaction_report(request, report_id):
    """
    Update an existing transaction report
    """
    try:
        project_id = request.data.get('project_id')
        if not project_id:
            return Response({
                'error': 'Project ID is required',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        report_ref = db.reference(f'projects/{project_id}/transaction_reports/{report_id}')
        report = report_ref.get()

        if not report:
            return Response({
                'error': 'Report not found',
                'status': 'error'
            }, status=status.HTTP_404_NOT_FOUND)

        update_data = {
            'title': request.data.get('title', report.get('title')),
            'date': request.data.get('date', report.get('date')),
            'amount': request.data.get('amount', report.get('amount')),
            'type': request.data.get('type', report.get('type')),
            'status': request.data.get('status', report.get('status')),
            'details': request.data.get('details', report.get('details')),
            'updated_at': datetime.now().isoformat()
        }

        report_ref.update(update_data)

        return Response({
            'data': {
                'id': report_id,
                **update_data
            },
            'message': 'Transaction report updated successfully',
            'status': 'success'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print("Error:", str(e))  # Debug print
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_transaction_report(request, report_id):
    """
    Delete a transaction report
    """
    try:
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({
                'error': 'Project ID is required',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        report_ref = db.reference(f'projects/{project_id}/transaction_reports/{report_id}')
        report = report_ref.get()

        if not report:
            return Response({
                'error': 'Report not found',
                'status': 'error'
            }, status=status.HTTP_404_NOT_FOUND)

        report_ref.delete()
        return Response({
            'message': 'Transaction report deleted successfully',
            'status': 'success'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print("Error:", str(e))  # Debug print
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateFinancialReportView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Create a new financial report
        """
        print("Method:", request.method)  # Debug print
        print("Request Data:", request.data)  # Debug print
        
        try:
            data = request.data

            # Validate required fields
            required_fields = ['project_id', 'title', 'date', 'amount', 'details']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return Response({
                    'error': f'Missing required fields: {", ".join(missing_fields)}',
                    'status': 'error',
                    'received_data': data
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate title
            valid_titles = ['BALANCE_SHEET', 'INCOME_STATEMENT', 'CASH_FLOW']
            if data.get('title') not in valid_titles:
                return Response({
                    'error': f'Invalid title. Must be one of: {", ".join(valid_titles)}',
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)

            report_data = {
                'title': data.get('title'),
                'date': data.get('date'),
                'amount': data.get('amount'),
                'type': 'MONTHLY',  # All financial reports are monthly
                'status': 'COMPLETED',  # All financial reports are completed
                'details': data.get('details'),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            print("Report Data to be saved:", report_data)  # Debug print

            # Add report to Firebase
            reports_ref = db.reference(f'projects/{data.get("project_id")}/financial_reports')
            new_report = reports_ref.push(report_data)

            return Response({
                'data': {
                    'id': new_report.key,
                    **report_data
                },
                'message': 'Financial report created successfully',
                'status': 'success'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print("Error:", str(e))  # Debug print
            return Response({
                'error': str(e),
                'status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_financial_reports(request, project_id):
    """
    Get all financial reports for a project
    """
    try:
        # Get reports from Firebase
        reports_ref = db.reference(f'projects/{project_id}/financial_reports')
        reports = reports_ref.get()

        if not reports:
            return Response({
                'message': 'No financial reports found',
                'data': [],
                'status': 'success'
            }, status=status.HTTP_200_OK)

        # Convert reports to list
        reports_list = []
        for report_id, report in reports.items():
            reports_list.append({
                'id': report_id,
                **report
            })

        return Response({
            'data': reports_list,
            'message': 'Financial reports retrieved successfully',
            'status': 'success'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([AllowAny])
def update_financial_report(request, report_id):
    """
    Update a financial report
    """
    try:
        data = request.data
        project_id = data.get('project_id')

        if not project_id:
            return Response({
                'error': 'Project ID is required',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get existing report
        reports_ref = db.reference(f'projects/{project_id}/financial_reports/{report_id}')
        existing_report = reports_ref.get()

        if not existing_report:
            return Response({
                'error': 'Report not found',
                'status': 'error'
            }, status=status.HTTP_404_NOT_FOUND)

        # Update report data
        update_data = {
            'title': data.get('title', existing_report.get('title')),
            'date': data.get('date', existing_report.get('date')),
            'amount': data.get('amount', existing_report.get('amount')),
            'details': data.get('details', existing_report.get('details')),
            'updated_at': datetime.now().isoformat()
        }

        # Update in Firebase
        reports_ref.update(update_data)

        return Response({
            'data': {
                'id': report_id,
                **update_data
            },
            'message': 'Financial report updated successfully',
            'status': 'success'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_financial_report(request, report_id):
    """
    Delete a financial report
    """
    try:
        project_id = request.query_params.get('project_id')

        if not project_id:
            return Response({
                'error': 'Project ID is required',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Delete from Firebase
        reports_ref = db.reference(f'projects/{project_id}/financial_reports/{report_id}')
        reports_ref.delete()

        return Response({
            'message': 'Financial report deleted successfully',
            'status': 'success'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_financial_report(request):
    """
    Create a new financial report
    """
    print("Method:", request.method)  # Debug print
    print("Request Data:", request.data)  # Debug print
    
    try:
        data = request.data

        # Validate required fields
        required_fields = ['project_id', 'title', 'date', 'amount', 'details']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return Response({
                'error': f'Missing required fields: {", ".join(missing_fields)}',
                'status': 'error',
                'received_data': data
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate title
        valid_titles = ['BALANCE_SHEET', 'INCOME_STATEMENT', 'CASH_FLOW']
        if data.get('title') not in valid_titles:
            return Response({
                'error': f'Invalid title. Must be one of: {", ".join(valid_titles)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        report_data = {
            'title': data.get('title'),
            'date': data.get('date'),
            'amount': data.get('amount'),
            'type': 'MONTHLY',  # All financial reports are monthly
            'status': 'COMPLETED',  # All financial reports are completed
            'details': data.get('details'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        print("Report Data to be saved:", report_data)  # Debug print

        # Add report to Firebase
        reports_ref = db.reference(f'projects/{data.get("project_id")}/financial_reports')
        new_report = reports_ref.push(report_data)

        return Response({
            'data': {
                'id': new_report.key,
                **report_data
            },
            'message': 'Financial report created successfully',
            'status': 'success'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print("Error:", str(e))  # Debug print
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_transaction_report(request):
    """
    Create a new transaction report
    """
    print("Method:", request.method)  # Debug print
    print("Request Data:", request.data)  # Debug print
    
    try:
        data = request.data

        # Validate required fields
        required_fields = ['project_id', 'title', 'date', 'amount', 'type', 'details']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return Response({
                'error': f'Missing required fields: {", ".join(missing_fields)}',
                'status': 'error',
                'received_data': data
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate title
        valid_titles = ['TRANSACTION_HISTORY', 'SETTLEMENT_REPORT', 'TRADING_ACTIVITY']
        if data.get('title') not in valid_titles:
            return Response({
                'error': f'Invalid title. Must be one of: {", ".join(valid_titles)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate type
        valid_types = ['DAILY', 'WEEKLY']
        if data.get('type') not in valid_types:
            return Response({
                'error': f'Invalid type. Must be one of: {", ".join(valid_types)}',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)

        report_data = {
            'title': data.get('title'),
            'date': data.get('date'),
            'amount': data.get('amount'),
            'type': data.get('type'),
            'status': data.get('status', 'ACTIVE'),
            'details': data.get('details'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        print("Report Data to be saved:", report_data)  # Debug print

        # Add report to Firebase
        reports_ref = db.reference(f'projects/{data.get("project_id")}/transaction_reports')
        new_report = reports_ref.push(report_data)

        return Response({
            'data': {
                'id': new_report.key,
                **report_data
            },
            'message': 'Transaction report created successfully',
            'status': 'success'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print("Error:", str(e))  # Debug print
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

