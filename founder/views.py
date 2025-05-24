from firebase_admin import db
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
import uuid
from rest_framework.parsers import MultiPartParser, FormParser
from Investa.utils import upload_image_to_drive, upload_video_to_drive, upload_file_to_drive
import os
from rest_framework import status
from django.conf import settings


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def insert_project(request):
    data = request.data
    form_id = str(uuid.uuid4())

    image_file = request.FILES.get("image")
    video_file = request.FILES.get("video")

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
            "service": data.get("service"),
            "number_of_employees": data.get("number_of_employees"),
            "years_in_business": data.get("years_in_business"),
            "annual_return": data.get("annual_return"),
            "website": data.get("website"),
            "stage": data.get("stage"),
            "partners": data.get("partners"),
            "required_amount_of_investment": data.get("required_amount_of_investment"),
            "percentage_for_partnership": data.get("percentage_for_partnership"),
            "brief_desc": data.get("brief_desc"),
            "image": image_url,
            "video": data.get("video"),
        })

        return Response({
            "message": "Form submitted successfully!",
            "image_url": image_url
        })

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def insert_business_details(request):
    data = request.data
    form_id = str(uuid.uuid4())  # unique ID for this submission

    # رفع ملف الأربع ركائز (اختياري)
    file = request.FILES.get("four_pillars_file")
    file_url = ""
    if file:
        temp_path = f"{form_id}_pillars.pdf"
        with open(temp_path, 'wb+') as f:
            for chunk in file.chunks():
                f.write(chunk)
        file_url = upload_file_to_drive(temp_path, f"{form_id}_pillars.pdf")  # ممكن تعمل دالة خاصة للملفات غير الفيديو
        os.remove(temp_path)

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
            "net_profit": data.get("net_profit"),
            "repeat_purchase_rate": data.get("repeat_purchase_rate"),
            "branches_count": data.get("branches_count"),
            "customers": data.get("customers"),
            "customer_growth": data.get("customer_growth"),
            "operating_costs": data.get("operating_costs"),
            "debt_to_profit_ratio": data.get("debt_to_profit_ratio"),

            "market_size_egp": data.get("market_size_egp"),
            "funding_egp": data.get("funding_egp"),

            "strengths": data.get("strengths"),
            "weaknesses": data.get("weaknesses"),
            "opportunities": data.get("opportunities"),
            "threats": data.get("threats"),
            "competitors": data.get("competitors"),

            "four_pillars_file_url": file_url
        })

        return Response({"message": "Business details submitted successfully", "file_url": file_url})

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
