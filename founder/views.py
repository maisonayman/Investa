from firebase_admin import db
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
import uuid
from rest_framework.parsers import MultiPartParser, FormParser
from Investa.utils import upload_image_to_drive, upload_video_to_drive, upload_file_to_drive
from rest_framework import status
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework.views import APIView
from collections import defaultdict
from datetime import datetime



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
    project_id = str(uuid.uuid4())  # ONE ID for all sections

    try:
        # --- Upload logo
        project_logo_url = ""
        if "projectLogoFileName" in files:
            project_logo_url = upload_image_to_drive(
                files["projectLogoFileName"],
                f"{project_id}_project_logo.jpg",
                folder_id=settings.FOLDER_ID_FOR_PROJECT_PIC
            )

        # --- Upload media files using updated upload_file_to_drive()
        def upload_optional_doc(field_name, filename_suffix):
            file = files.get(field_name)
            if file:
                return upload_file_to_drive(
                    file,
                    f"{project_id}_{filename_suffix}"
                )
            return ""

        commercial_reg_url = upload_optional_doc("commercialRegFile", "commercial_reg.pdf")
        financial_summary_url = upload_optional_doc("financialSummaryFile", "financial_summary.pdf")
        business_plan_url = upload_optional_doc("simplifiedBusinessPlanFile", "business_plan.pdf")

        # --- Project Info
        project_info = {
            "projectName": data.get("projectName"),
            "briefDescription": data.get("briefDescription"),
            "detailedDescription": data.get("detailedDescription"),
            "projectCategory": data.get("projectCategory"),
            "projectStartDate": data.get("projectStartDate"),
            "geographicalLocation": data.get("geographicalLocation"),
            "teamSize": data.get("teamSize"),
            "annualRevenue": data.get("annual"),
            "monthlyGrowthRate": data.get("monthlygrowthrate"),
            "netProfit": data.get("netprofit"),
            "currentCustomers": data.get("numcustomers"),
            "repeatPurchaseRate": data.get("purchaserate"),
            "numberOfBranches": data.get("branchesnum"),
            "customerGrowthRate": data.get("growthrate"),
            "churnRate": data.get("churnrate"),
            "monthlyOperatingCosts": data.get("monthlyoperatingcosts"),
            "debtToEquityRatio": data.get("depttoequity"),
            "fundingNeeded": data.get("fundingneeded"),
            "ownershipPercentage": data.get("ownershipPercentage"),
            "investmentType": data.get("investmentType"),
            "totalInvestorsAllowed": data.get("totalInvestorsAllowed"),
            "maxInvestorShort": data.get("maxInvestorShort"),
            "maxInvestorLong": data.get("maxInvestorLong"),
            "projectLogoUrl": project_logo_url,
        }

        # --- Analysis Info
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

        # --- Media Info
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

        # --- Save to Firebase using the same ID
        db.reference(f'projects/{project_id}').set(project_info)
        db.reference(f'analysis/{project_id}').set(analysis_info)
        db.reference(f'media_and_attachments/{project_id}').set(media_info)

        return Response({
            "message": "success",
            "projectId": project_id
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
def send_phase3_email(request):
    data = request.data
    email = data.get('email')
    user_id = data.get('user_id')  # optional for tracking

    if not email:
        return Response({"error": "Email is required"}, status=400)

    # Render the email HTML
    html_content = render_to_string('emails/phase3_email.html', {
        'upload_link': f'https://yourdomain.com/upload-phase1/?user={user_id or ""}'
    })

    subject = "Phase 3: Upload Your Physical Store Picture"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [email]

    try:
        msg = EmailMultiAlternatives(subject, "", from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return Response({"message": "Phase 3 email sent successfully."}, status=200)
    except Exception as e:
        return Response({"error": "Failed to send email", "details": str(e)}, status=500)


@api_view(['GET'])
def founder_home(request, project_id):
    try:
        # Fetch data from Firebase
        project_data = db.reference(f'projects/{project_id}').get() or {}
        analysis_data = db.reference(f'analysis/{project_id}').get() or {}
        media_data = db.reference(f'media_and_attachments/{project_id}').get() or {}

        if not project_data:
            return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Compose the response matching your Flutter expected format:
        response_data = {
            "user_data": {
                "name": project_data.get("projectName", ""),
                "profile_picture_url": project_data.get("projectLogoUrl", "")
            },
            "overview_data": {
                "project_status": project_data.get("projectStatus", "قيد التقدم"),  # Example, you may add this to project_info when saving
                "progress_percentage": project_data.get("progressPercentage", "80%"),
                "num_investors": project_data.get("numInvestors", 0),
                "total_funding": project_data.get("totalFunding", "0 L.E"),
                "overall_project_rating": project_data.get("overallProjectRating", "0")
            },

            "additional_info": {
                "funding_goal": analysis_data.get("fundingGoal", ""),
                "completed_funding": analysis_data.get("completedFunding", ""),
                "expected_success_rate": analysis_data.get("expectedSuccessRate", ""),
                "investment_state": analysis_data.get("investmentState", ""),
                "total_investors_allowed": analysis_data.get("totalInvestorsAllowed", 0),
                "max_short_term": analysis_data.get("maxInvestorShort", 0),
                "max_long_term": analysis_data.get("maxInvestorLong", 0),
                "minimum_investment": analysis_data.get("minimumInvestment", ""),
                "maximum_investment": analysis_data.get("maximumInvestment", ""),
                "minimum_short_term": analysis_data.get("minimumShortTerm", ""),
                "minimum_long_term": analysis_data.get("minimumLongTerm", ""),
                "deadline": analysis_data.get("deadline", ""),
                "store_type": analysis_data.get("storeType", ""),
                "location": project_data.get("geographicalLocation", ""),
                "website": media_data.get("projectWebsiteLinks", ""),
                "social_media": media_data.get("socialMedia", {
                    "twitter": "",
                    "facebook": "",
                    "instagram": "",
                    "linkedin": ""
                }),
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def founder_investment_graph(request, founder_id):
    # Step 1: Get all projects for this founder
    projects_ref = db.reference('projects')
    projects_data = projects_ref.get() or {}

    founder_project_ids = [
        pid for pid, pdata in projects_data.items()
        if pdata.get('founder_id') == founder_id
    ]

    # Step 2: Get all investments
    invested_ref = db.reference('invested_projects')
    investments = invested_ref.get() or {}

    # Step 3: Prepare monthly data
    monthly_data = defaultdict(lambda: {"total_invested": 0, "total_profit": 0})

    for key, inv in investments.items():
        if inv.get('project_id') in founder_project_ids:
            timestamp = inv.get('timestamp')
            if not timestamp:
                continue  # skip if no timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                month_key = dt.strftime("%Y-%m")  # e.g., "2025-03"
            except:
                continue

            invested_amount = float(inv.get('amount_invested', 0))
            profit = float(inv.get('profit', 0))

            monthly_data[month_key]["total_invested"] += invested_amount
            monthly_data[month_key]["total_profit"] += profit

    # Step 4: Format response with ROI
    graph_data = []
    for month in sorted(monthly_data.keys()):
        total = monthly_data[month]["total_invested"]
        profit = monthly_data[month]["total_profit"]
        roi = (profit / total) if total > 0 else 0
        graph_data.append({
            "month": month,
            "investment_return": round(roi, 2),         # e.g. 0.25 for 25%
            "total_invested": round(total, 2)
        })

    return Response(graph_data)


@api_view(['GET'])
def get_project(request, project_id):
    try:
        # Get project data from Firebase Realtime Database
        project_ref = db.reference(f'projects/{project_id}')
        project_data = project_ref.get()

        if project_data:
            return Response(project_data, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionsAPI(APIView):
    def get(self, request):
        ref = db.reference('transactions')
        data = ref.get()
        total_income = 0
        total_expenses = 0
        transactions = []

        if data:
            for key, tx in data.items():
                tx["id"] = key
                amount = float(tx["amount"])
                if tx["type"] == "Income":
                    total_income += amount
                elif tx["type"] == "Expense":
                    total_expenses += amount
                transactions.append(tx)

        net_profit = total_income - total_expenses
        profit_percent = round((net_profit / total_income) * 100, 1) if total_income else 0

        return Response({
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_profit": net_profit,
            "profit_percent": profit_percent,
            "transactions": transactions
        }, status=status.HTTP_200_OK)

    def put(self, request):
        try:
            ref = db.reference('transactions')
            data = request.data
            tx_id = data.get("id")
            if not tx_id:
                return Response({"error": "يجب إرسال id"}, status=status.HTTP_400_BAD_REQUEST)

            tx_ref = ref.child(tx_id)
            tx_ref.update({
                "date": data["date"],
                "type": data["type"],
                "description": data["description"],
                "amount": data["amount"],
                "payment_method": data["payment_method"],
                "responsible": data["responsible"]
            })

            return Response({"message": "تم التعديل بنجاح"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            ref = db.reference('transactions')
            data = request.data
            tx_id = data.get("id")
            if not tx_id:
                return Response({"error": "يجب إرسال id"}, status=status.HTTP_400_BAD_REQUEST)

            tx_ref = ref.child(tx_id)
            tx_ref.delete()

            return Response({"message": "تم الحذف بنجاح"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
  
 
@api_view(['POST'])
def add_product(request):
    try:
        data = request.data
        ref = db.reference('products')
        ref.push({
            "product_name": data.get("product_name"),
            "price": data.get("price"),
            "roi": data.get("roi"),
            "available_qty": data.get("available_qty"),
            "sold_qty": data.get("sold_qty")
        })
        return Response({"status": "success", "message": "Product added successfully"})
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)

