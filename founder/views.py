from firebase_admin import db
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
import uuid
from rest_framework.parsers import MultiPartParser, FormParser
from Investa.utils import upload_image_to_drive, upload_video_to_drive, upload_file_to_drive
import os
from rest_framework import status
from django.conf import settings
from django.http import JsonResponse


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

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def create_project(request):
    data = request.data
    files = request.FILES
    project_id = str(uuid.uuid4())

    try:
        project_logo_url = ""
        if "projectLogoFileName" in files:
            project_logo_url = upload_image_to_drive(
                files["projectLogoFileName"], f"{project_id}_project_logo.jpg", folder_id=settings.FOLDER_ID_FOR_PROJECT_PIC
            )

        project_info = {
            "projectName": data.get("projectName"),
            "briefDescription": data.get("briefDescription"),
            "detailedDescription": data.get("detailedDescription"),
            "projectCategory": data.get("projectCategory"),
            "projectStartDate": data.get("projectStartDate"),
            "geographicalLocation": data.get("geographicalLocation"),
            "teamSize": data.get("teamSize"),
            "projectLogoUrl": project_logo_url,

            # القسم المالي
            "annualRevenue": data.get("annualRevenue"),
            "monthlyGrowthRate": data.get("monthlyGrowthRate"),
            "netProfit": data.get("netProfit"),
            "currentCustomers": data.get("currentCustomers"),
            "repeatPurchaseRate": data.get("repeatPurchaseRate"),
            "numberOfBranches": data.get("numberOfBranches"),
            "customerGrowthRate": data.get("customerGrowthRate"),
            "churnRate": data.get("churnRate"),
            "monthlyOperatingCosts": data.get("monthlyOperatingCosts"),
            "debtToEquityRatio": data.get("debtToEquityRatio"),
            "fundingNeeded": data.get("fundingNeeded"),
            "ownershipPercentage": data.get("ownershipPercentage"),
            "investmentType": data.get("investmentType"),
            "totalInvestorsAllowed": data.get("totalInvestorsAllowed"),
            "maxInvestorShort": data.get("maxInvestorShort"),
            "maxInvestorLong": data.get("maxInvestorLong"),
        }

        db.reference(f'projects/{project_id}').set(project_info)

        return Response({"message": "تم إنشاء المشروع بنجاح", "projectId": project_id})
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['POST'])
def create_analysis(request):
    data = request.data
    analysis_id = str(uuid.uuid4())
    project_id = data.get("projectId")

    if not project_id:
        return Response({"error": "يجب إرسال projectId"}, status=400)

    try:
        analysis_info = {
            "projectId": project_id,
            "strengths": data.get("strengths"),
            "weaknesses": data.get("weaknesses"),
            "opportunities": data.get("opportunities"),
            "threats": data.get("threats"),
            "businessModel": data.get("businessModel"),
            "marketingStrategy": data.get("marketingStrategy"),
            "useOfFundsPlan": data.get("useOfFundsPlan"),
            "competitors": data.get("competitors"),
        }

        db.reference(f'analysis/{analysis_id}').set(analysis_info)

        return Response({"message": "تم حفظ تحليل المشروع", "analysisId": analysis_id})
    
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def create_media_and_attachments(request):
    data = request.data
    files = request.FILES
    media_id = str(uuid.uuid4())
    project_id = data.get("projectId")

    if not project_id:
        return Response({"error": "يجب إرسال projectId"}, status=400)

    try:
        def upload_optional_file(field_name, filename_prefix):
            file = files.get(field_name)
            if file:
                return upload_image_to_drive(file, f"{media_id}_{filename_prefix}", folder_id=settings.FOLDER_ID_FOR_PROJECT_PIC)
            return ""

        commercial_reg_url = upload_optional_file("commercialRegFile", "commercial_reg.pdf")
        financial_summary_url = upload_optional_file("financialSummaryFile", "financial_summary.pdf")
        business_plan_url = upload_optional_file("simplifiedBusinessPlanFile", "business_plan.pdf")

        media_info = {
            "projectId": project_id,
            "photosVideosMedia": data.get("photosVideosMedia"),
            "customerTestimonials": data.get("customerTestimonials"),
            "projectWebsiteLinks": data.get("projectWebsiteLinks"),
            "awardsCertifications": data.get("awardsCertifications"),
            "uploadedMediaFileNames": data.get("uploadedMediaFileNames"),
            "commercialRegFileUrl": commercial_reg_url,
            "financialSummaryFileUrl": financial_summary_url,
            "simplifiedBusinessPlanFileUrl": business_plan_url,
        }

        db.reference(f'media_and_attachments/{media_id}').set(media_info)

        return Response({"message": "تم رفع المرفقات بنجاح", "mediaId": media_id})
    
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    