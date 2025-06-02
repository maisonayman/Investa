from firebase_admin import db
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
import uuid
from rest_framework.parsers import MultiPartParser, FormParser
from Investa.utils import upload_image_to_drive, upload_video_to_drive, upload_file_to_drive
import os
from rest_framework import status
from django.conf import settings
<<<<<<< HEAD
=======
from django.http import JsonResponse
>>>>>>> 0d888d36df8110df0fc53ea293c02b38dc3173fe


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def insert_project(request):
    data = request.data
    form_id = str(uuid.uuid4())

    image_file = request.FILES.get("project_image")

    try:
        # Upload image
        if image_file:
            image_url = upload_image_to_drive(
                image_file,
                f"{form_id}_image.jpg",
                folder_id=settings.FOLDER_ID_FOR_PROJECT_PIC
            )
        else:
            image_url = ""


        # Save data in Firebase
        db.reference(f'companies/{form_id}').set({
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
            "email": data.get("email"),
            "phone_number": data.get("phone_number"),
            "date_of_birth": data.get("date_of_birth"),
            "gender": data.get("gender"),
            "city": data.get("city"),
            "company_name": data.get("company_name"),
            "service": data.get("service_description"),
            "number_of_employees": data.get("employees_count"),
            "years_in_business": data.get("years_in_business"),
            "annual_return": data.get("annual_return"),
            "website": data.get("company_website"),
            "business_type": data.get("business_type"),
            "stage": data.get("business_stage"),
            "has_partners": data.get("has_partners"),
            "required_amount_of_investment": data.get("estimated_investment_amount"),
            "brief_desc": data.get("project_description"),
            "image": image_url,
            "video": data.get("video_link"),
            "robot_or_not": data.get("is_not_robot"),
        })

        return Response({
            "message": "Form submitted successfully!",
            "image_url": image_url
        })

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def insert_business_details(request):
    data = request.data
    form_id = str(uuid.uuid4())  # unique ID for this submission

    try:
        db.reference(f'business_details/{form_id}').set({
            "funding_egp": data.get("funding_egp"),
            "equity_percentage": data.get("equity_percentage"),
            "duration_months": data.get("duration_months"),
            "industry": data.get("industry"),
            "target_market": data.get("target_market"),
            "business_model": data.get("business_model"),
            "founder_experience_years": data.get("founder_experience_years"),
            "team_size": data.get("team_size"),
            "revenue": data.get("revenue"),
            "revenue_growth": data.get("revenue_growth"),
            "profit_margin": data.get("profit_margin"),
            "net_profit": data.get("profit"),
            "repeat_purchase_rate": data.get("repeat_purchase_rate"),
            "branches_count": data.get("branches_count"),
            "customers": data.get("customers"),
            "customer_growth": data.get("customer_growth"),
            "operating_costs": data.get("operating_costs"),
            "debt_to_profit_ratio": data.get("debt_to_profit_ratio"),
            "market_size_egp": data.get("market_size_egp"),
            "previous_funding_egp": data.get("previous_funding_egp"),
            "strengths": data.get("strengths"),
            "weaknesses": data.get("weaknesses"),
            "opportunities": data.get("opportunities"),
            "threats": data.get("threats"),
            "competitors": data.get("competitors_info"),
            "four_pillars": data.get("four_pillars_description")
        })

        return Response({"message": "Business details submitted successfully"})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


<<<<<<< HEAD
=======
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


>>>>>>> 0d888d36df8110df0fc53ea293c02b38dc3173fe


    