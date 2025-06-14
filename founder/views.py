from firebase_admin import db
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes, permission_classes
import uuid
from rest_framework.parsers import MultiPartParser, FormParser
from Investa.utils import upload_image_to_drive, get_user_data, upload_file_to_drive, get_founder_projects, get_investments_for_projects
from rest_framework import status
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework.views import APIView
from collections import defaultdict
from datetime import datetime
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
import os
import pandas as pd
import joblib
from datetime import datetime
from firebase_admin import db
from rest_framework.decorators import api_view
from rest_framework.response import Response


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
        user_id = data.get("user_id")
        if not user_id:
            return Response({"error": "user_id is required."}, status=400)

        # --- Upload logo
        project_logo_url = ""
        if "projectLogoFileName" in files:
            project_logo_url = upload_image_to_drive(
                files["projectLogoFileName"],
                f"{project_id}_project_logo.jpg",
                folder_id=settings.FOLDER_ID_FOR_PROJECT_PIC
            )

        # --- Upload optional docs
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

        # --- Project Info (added userId)
        project_info = {
            "userId": user_id,
            "projectName": data.get("projectName"),
            "briefDescription": data.get("briefDescription"),
            "detailedDescription": data.get("detailedDescription"),
            "projectCategory": data.get("projectCategory"),
            "projectStartDate": data.get("projectStartDate"),
            "geographicalLocation": data.get("geographicalLocation"),
            "teamSize": data.get("teamSize"),
            "annualRevenue": data.get("annualRevenue"),
            "monthlyGrowthRate": data.get("monthlyGrowthRate"),
            "netProfit": data.get("netProfit"),
            "currentCustomers": data.get("currentCustomers"),
            "repeatPurchaseRate": data.get("repeatPurchaseRate"),
            "numberOfBranches": data.get("numberOfBranches"),
            "customerGrowthRate": data.get("customerGrowthRate"),
            "churnRate": data.get("churnRate"),
            "monthlyOperatingCosts": data.get("monthlyOperatingCosts"),
            "debtToEquityRatio": data.get("deptToEquityRatio"),  # spelling في الصورة مكتوب "dept" مش "debt"
            "fundingNeeded": data.get("fundingNeeded"),
            "ownershipPercentage": data.get("ownershipPercentage"),
            "investmentType": data.get("investmentType"),
            "totalInvestorsAllowed": data.get("totalInvestorsAllowed"),
            "maxInvestorShort": data.get("maxInvestorsShort"),
            "maxInvestorLong": data.get("maxInvestorsLong"),
            "projectLogoUrl": project_logo_url,  # حط اللوجو من عندك هنا، الاسم في الداتا: projectLogoFileName
        }


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

        # --- Save to Firebase
        db.reference(f'projects/{project_id}').set(project_info)
        db.reference(f'analysis/{project_id}').set(analysis_info)
        db.reference(f'media_and_attachments/{project_id}').set(media_info)

        # (اختياري) احفظ تحت المستخدم كمان:
        db.reference(f'users/{user_id}/projects/{project_id}').set({"created": True})

        return Response({
            "message": "success",
            "projectId": project_id
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)



@api_view(['POST'])
def send_phase3_email(request):
    data = request.data
    user_id = data.get('user_id')

    if not user_id:
        return Response({"error": "User ID is required"}, status=400)

    # Fetch from Firebase
    user_data = get_user_data(user_id)
    if not user_data:
        return Response({"error": "User not found in Firebase"}, status=404)

    full_name = user_data.get('full_name', 'User')
    first_two_names = " ".join(full_name.split()[:2])

    email = user_data.get('email')

    if not email:
        return Response({"error": "Email is missing in Firebase user data"}, status=400)

    # Render the email
    html_content = render_to_string('emails/phase3_email.html', {
        "full_name": first_two_names,
        'email': email,
        'upload_link': f'https://yourdomain.com/upload-phase1/?user={user_id}'
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


@api_view(['GET'])
def founder_dashboard_overview(request, user_id):
    try:
        # Step 1: Get founder's projects
        projects = get_founder_projects(user_id)
        if not projects:
            return Response({
                "total_invested_amount": 0,
                "number_of_investors": 0,
                "revenue": 0,
                "realized_profit": 0,
                "message": "No projects found for this founder."
            }, status=200)

        # Extract project_ids from the list of project dictionaries
        project_ids = [p.get('project_id') for p in projects if p.get('project_id')]

        if not project_ids:
            return Response({
                "total_invested_amount": 0,
                "number_of_investors": 0,
                "revenue": 0,
                "realized_profit": 0,
                "message": "No valid project IDs found for this founder."
            }, status=200)

        # Step 2: Get investments related to these projects
        investments = get_investments_for_projects(project_ids) # Pass the list of IDs
        if not investments:
            return Response({
                "total_invested_amount": 0,
                "number_of_investors": 0,
                "revenue": 0,
                "realized_profit": 0,
                "message": "No investments found for the founder's projects."
            }, status=200)

        total_invested = 0
        investor_ids = set()
        total_roi = 0
        total_realized_profit = 0

        # Step 3: Process investments
        for inv in investments:
            # Handle invested_amount (string to float)
            invested_amount_str = inv.get('invested_amount', '0')
            try:
                total_invested += float(invested_amount_str)
            except ValueError:
                print(f"Warning: Could not convert invested_amount '{invested_amount_str}' to float for investment {inv.get('project_id')}")

            # Collect unique investor IDs
            investor_user_id = inv.get('user_id')
            if investor_user_id:
                investor_ids.add(investor_user_id)

            # Handle ROI (string to float) - assuming 'roi' is a number string like "100" (for 100%)
            roi_str = inv.get('roi', '0')
            try:
                total_roi += float(roi_str)
            except ValueError:
                print(f"Warning: Could not convert roi '{roi_str}' to float for investment {inv.get('project_id')}")

            # Handle current_profit ("30%") - needs parsing
            current_profit_str = inv.get('current_profit', '0%')
            if isinstance(current_profit_str, str) and '%' in current_profit_str:
                current_profit_str = current_profit_str.replace('%', '') # Remove '%'
            try:
                profit_value = float(current_profit_str)
                total_realized_profit += profit_value
            except ValueError:
                print(f"Warning: Could not convert current_profit '{current_profit_str}' to float for investment {inv.get('project_id')}")

        return Response({
            "total_invested_amount": total_invested,
            "number_of_investors": len(investor_ids),
            "revenue": total_roi,
            "realized_profit": total_realized_profit
        }, status=200)

    except Exception as e:
        import traceback
        print(f"Error in founder_dashboard_overview API for user {user_id}: {e}")
        traceback.print_exc() # Prints the full traceback to the console/logs
        return JsonResponse({'error': f'An internal server error occurred: {e}'}, status=500)


@api_view(['GET'])
def investment_return_vs_comparison(request, user_id):
    projects = get_founder_projects(user_id)
    project_ids = [p.get('project_id') for p in projects]
    investments = get_investments_for_projects(project_ids)

    month_counts = defaultdict(int)
    month_data = defaultdict(lambda: {"roi": 0.0, "count": 0})

    single_entries = []

    for inv in investments:
        date_str = inv.get("invested_at", "")
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            except:
                continue

        month_label = date_obj.strftime('%b')  # e.g. 'Jun'
        roi = float(inv.get('roi', 0))
        comparison = roi * 0.9  # مثال: المقارنة 90% من العائد

        month_counts[month_label] += 1
        month_data[month_label]["roi"] += roi
        month_data[month_label]["count"] += 1

        # لو الشهر ظهر مرة واحدة بس لحد دلوقتي → خزّنه كـ فردي
        if month_data[month_label]["count"] == 1:
            single_entries.append({
                "month": month_label,
                "roi": roi,
                "comparison": comparison
            })

    # هنجمع الشهري اللي متكرر أكتر من مرة فقط
    grouped_entries = []
    for month, info in month_data.items():
        if month_counts[month] > 1:
            grouped_entries.append({
                "month": month,
                "roi": info["roi"],
                "comparison": info["roi"] * 0.9  # المقارنة 90% من العائد المجمع
            })

    # النهائي: دمج البيانات الفردية مع المجمعه
    all_data = grouped_entries + [
        entry for entry in single_entries if month_counts[entry["month"]] == 1
    ]

    # ترتيب حسب الشهر
    all_data.sort(key=lambda x: datetime.strptime(x["month"], "%b").month)
    investment_return = defaultdict(float)
    comparison_data = defaultdict(float)

    for inv in investments:
        try:
            invested_date = datetime.strptime(inv.get('invested_at'), "%Y-%m-%d")
            month = invested_date.strftime('%b')
        except Exception:
            month = "Jan"

        roi = float(inv.get('roi', 30))
        investment_return[month] += roi

        # 👇 هنا بنحسب قيمة المقارنة كمثال: 90% من ROI الفعلي
        comparison_data[month] += roi * 0.9

    return Response({
        "dates": [entry["month"] for entry in all_data],
        "investment_return": [entry["roi"] for entry in all_data],
        "comparison_data": [entry["comparison"] for entry in all_data]
    })


@api_view(['GET'])
def portfolio_performance(request, user_id):
    try:
        projects = get_founder_projects(user_id)
        project_ids_for_filter = [p.get('project_id') for p in projects if p.get('project_id')]
        investments = get_investments_for_projects(project_ids_for_filter)

        performance = defaultdict(float)

        for inv in investments:
            invested_at_str = inv.get('invested_at')
            month_abbr = 'unknown_month' # Default value if parsing fails

            if invested_at_str and isinstance(invested_at_str, str):
                try:
                    # Parse the string to a datetime object
                    dt_object = datetime.strptime(invested_at_str, "%Y-%m-%d %H:%M:%S")
                    # Format to get the abbreviated month name (e.g., "Jan", "Feb")
                    month_abbr = dt_object.strftime("%b")
                except ValueError:
                    # Handle cases where the date string is malformed
                    print(f"Warning: Could not parse date from invested_at '{invested_at_str}' for investment {inv.get('project_id')}")
                    month_abbr = 'invalid_date' # Or handle as per your requirement

            current_portfolio_value = 0.0
            invested_amount_str = inv.get('invested_amount', '0')
            current_profit_str = inv.get('current_profit', '0%')

            try: current_portfolio_value += float(invested_amount_str)
            except ValueError: pass

            if isinstance(current_profit_str, str) and '%' in current_profit_str:
                current_profit_str = current_profit_str.replace('%', '')
            try: current_portfolio_value += float(current_profit_str)
            except ValueError: pass

            performance[month_abbr] += current_portfolio_value

        return Response(performance, status=200)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'An internal server error occurred: {e}'}, status=500)
    
    
@api_view(['GET'])
def profit_margin_trend(request, user_id):
    projects = get_founder_projects(user_id)

    project_ids = [p.get('project_id') for p in projects if p.get('project_id')]
    investments = get_investments_for_projects(project_ids)

    margins = defaultdict(float)
    counts = defaultdict(int)

    for inv in investments:
        date_str = inv.get("invested_at", "")
        roi = inv.get("roi")

        if not roi:
            continue

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            month = date_obj.strftime('%b')  # e.g. 'Aug'
        except:
            month = "Unknown"

        try:
            roi_value = float(roi)
            margins[month] += roi_value
            counts[month] += 1
        except:
            continue

    sorted_months = sorted(margins.keys(), key=lambda m: datetime.strptime(m, "%b").month if m != "Unknown" else 13)
    average_margins = [round(margins[m] / counts[m], 2) for m in sorted_months]

    return Response({
        "dates": sorted_months,
        "profit_margins": average_margins
    })


@api_view(['GET'])
def monthly_finance(request, user_id):
    ref = db.reference(f'users/{user_id}/monthly_finance')
    data = ref.get()

    formatted_data = []
    if data:
        for month, values in data.items():
            formatted_data.append({
                "month": month.capitalize(),
                "revenue": values.get("revenue", 0),
                "loss": values.get("loss", 0)
            })

        month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        formatted_data.sort(key=lambda x: month_order.index(x["month"]))

    return Response(formatted_data)


class TransactionsAPI(APIView):
    def get(self, request, user_id):
        ref = db.reference(f'transactions/{user_id}')
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

    def post(self, request, user_id):
        try:
            data = request.data
            required_fields = ['date', 'type', 'description', 'amount', 'payment_method', 'responsible']

            missing = [field for field in required_fields if field not in data]
            if missing:
                return Response({"error": f"Missing fields: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)

            ref = db.reference(f'transactions/{user_id}')
            new_tx = ref.push({
                "date": data["date"],
                "type": data["type"],
                "description": data["description"],
                "amount": data["amount"],
                "payment_method": data["payment_method"],
                "responsible": data["responsible"]
            })

            return Response({"message": "success", "id": new_tx.key}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

 

class ProductsAPI(APIView):
    def get(self, request):
        try:
            ref = db.reference('products')
            data = ref.get()
            products = []

            if data:
                for key, item in data.items():
                    item["id"] = key
                    products.append(item)

            return Response(products, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            data = request.data
            ref = db.reference('products')
            new_product_ref = ref.push(data)
            product_id = new_product_ref.key

            return Response({
                "message": "product added succesfully",
                "product_id": product_id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            data = request.data
            product_id = data.get("id")
            if not product_id:
                return Response({"error": "يجب إرسال id"}, status=status.HTTP_400_BAD_REQUEST)

            ref = db.reference(f'products/{product_id}')
            ref.update(data)

            return Response({"message": "تم التعديل بنجاح"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            data = request.data
            product_id = data.get("id")
            if not product_id:
                return Response({"error": "يجب إرسال id"}, status=status.HTTP_400_BAD_REQUEST)

            ref = db.reference(f'products/{product_id}')
            ref.delete()

            return Response({"message": "تم الحذف بنجاح"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


from collections import defaultdict
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
import firebase_admin
from firebase_admin import db

@api_view(['GET'])
def investor_manager(request, user_id):
    founder_projects = get_founder_projects(user_id)
    founder_project_ids = [proj.get("project_id") for proj in founder_projects]

    inv_ref = db.reference("invested_projects")
    all_investments = inv_ref.get()

    investor_map = {}

    if all_investments:
        for inv_id, inv in all_investments.items():
            if inv.get("project_id") in founder_project_ids:
                investor_id = inv.get("user_id")
                user_ref = db.reference(f"users/{investor_id}")
                user_data = user_ref.get() or {}

                username = user_data.get("username", "Unknown")
                invested_amount = float(inv.get("invested_amount", 0))
                roi = float(inv.get("roi", 0))
                status = inv.get("status", "Unknown")
                date_str = inv.get("invested_at", "")
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
                except:
                    date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None

                if investor_id in investor_map:
                    investor_map[investor_id]["amount_invested"] += invested_amount
                    investor_map[investor_id]["roi"] += roi
                    # keep the latest date
                    if date and date > investor_map[investor_id]["date"]:
                        investor_map[investor_id]["date"] = date
                else:
                    investor_map[investor_id] = {
                        "username": username,
                        "amount_invested": invested_amount,
                        "roi": roi,
                        "date": date,
                        "status": status
                    }

    # convert to list and format date
    investors_data = []
    for item in investor_map.values():
        item["date"] = item["date"].isoformat() if item["date"] else ""
        investors_data.append(item)

    return Response({"investors": investors_data})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_revenue_growth(request, user_id):
    
    try:
        # هات مشاريع ال founder
        projects = get_founder_projects(user_id)
        if not projects:
            return Response({"message": "No projects found", "revenues": [], "dates": []}, status=200)

        all_revenue_entries = []
        for project in projects:
            project_id = project.get("project_id")
            revenue_ref = db.reference(f'projects/{project_id}/revenue_entries')
            entries = revenue_ref.get() or {}
            for entry in entries.values():
                all_revenue_entries.append(entry)

        if not all_revenue_entries:
            return Response({"message": "No revenue data found", "revenues": [], "dates": []}, status=200)

        monthly_totals = defaultdict(float)

        for entry in all_revenue_entries:
            date_str = entry.get("date")
            amount = float(entry.get("amount", 0))

            if not date_str or amount == 0:
                continue

            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                month_label = date_obj.strftime('%b')  # e.g., 'Jun'
            except:
                month_label = "Unknown"

            monthly_totals[month_label] += amount

        # Sort months in calendar order
        sorted_months = sorted(
            monthly_totals.keys(),
            key=lambda m: datetime.strptime(m, "%b").month if m != "Unknown" else 13
        )

        revenue_values = [round(monthly_totals[m], 2) for m in sorted_months]

        return Response({
            "dates": sorted_months,
            "revenues": revenue_values
        }, status=200)

    except Exception as e:
        return Response({
            "error": str(e),
            "status": "error"
        }, status=500)



@api_view(['POST'])
@permission_classes([AllowAny])
def add_revenue_entry(request):
    try:
        user_id = request.data.get('user_id')
        amount = request.data.get('amount')
        date = request.data.get('date')  # expected format: YYYY-MM-DD

        if not user_id or not amount or not date:
            return Response({
                'error': 'user_id, amount, and date are required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # استخدم utility function لجلب مشاريع المستخدم
        projects = get_founder_projects(user_id)
        if not projects:
            return Response({
                'error': 'No project found for this user.'
            }, status=status.HTTP_404_NOT_FOUND)

        # استخدم أول مشروع (لو في أكتر من مشروع ممكن نعدل لاحقًا)
        project_id = projects[0]['project_id']

        # Validate date format
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

        # Push revenue entry
        revenue_ref = db.reference(f'projects/{project_id}/revenue_entries')
        revenue_ref.push({
            'amount': amount,
            'date': date
        })

        return Response({
            'message': 'Revenue entry added successfully.',
            'project_id': project_id,
            'status': 'success'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





def load_model_components():
    """Load the trained model and preprocessing components"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(base_dir, 'saved_models')
    
    return {
        'model': joblib.load(os.path.join(model_dir, 'best_model_random_forest.pkl')),
        'scaler': joblib.load(os.path.join(model_dir, 'feature_scaler.pkl')),
        'encoders': joblib.load(os.path.join(model_dir, 'label_encoders.pkl')),
        'feature_names': joblib.load(os.path.join(model_dir, 'feature_names.pkl')),
        'categorical_columns': joblib.load(os.path.join(model_dir, 'categorical_columns.pkl'))
    }


def prepare_prediction_data(project_info, analysis_info):
    """Transform Firebase project data into model-compatible format"""
    # Handle potential missing or invalid numeric values
    def safe_float(value, default=0.0):
        try:
            return float(value) if value else default
        except (ValueError, TypeError):
            return default
    
    def safe_int(value, default=0):
        try:
            return int(value) if value else default
        except (ValueError, TypeError):
            return default
    
    # Calculate profit margin safely
    revenue = safe_float(project_info.get('annualRevenue'))
    profit = safe_float(project_info.get('netProfit'))
    profit_margin = profit / revenue if revenue > 0 else 0.0
    
    # USD conversion rate (approximate)
    usd_rate = 50.0
    
    return {
        'industry': project_info.get('projectCategory', 'Other'),
        'funding_egp': safe_float(project_info.get('fundingNeeded')),
        'equity_percentage': safe_float(project_info.get('ownershipPercentage')),
        'duration_months': 12,  # Default value
        'target_market': 'Regional',  # Default based on location
        'business_model': analysis_info.get('businessModel', 'B2C'),
        'founder_experience_years': 5,  # Default value
        'team_size': safe_int(project_info.get('teamSize', 1)),
        'traction': 'Medium',  # Default value
        'market_size_usd': 5000000,  # Default value
        'funding_usd': safe_float(project_info.get('fundingNeeded')) / usd_rate,
        'profit': profit,
        'repeat_purchase_rate': safe_float(project_info.get('repeatPurchaseRate')),
        'branches_count': safe_int(project_info.get('numberOfBranches')),
        'revenue': revenue,
        'customers': safe_int(project_info.get('currentCustomers')),
        'revenue_growth': safe_float(project_info.get('monthlyGrowthRate')),
        'profit_margin': profit_margin,
        'customer_growth': safe_float(project_info.get('customerGrowthRate')),
        'churn_rate': safe_float(project_info.get('churnRate')),
        'operating_costs': safe_float(project_info.get('monthlyOperatingCosts')),
        'debt_to_profit_ratio': safe_float(project_info.get('debtToEquityRatio'))
    }


def predict_investment_success(data_df, components):
    """Make predictions using the loaded model and preprocessors"""
    data_processed = data_df.copy()
    
    # Encode categorical variables
    for col in components['categorical_columns']:
        if col in data_processed.columns:
            encoder = components['encoders'][col]
            data_processed[col] = data_processed[col].astype(str)
            
            # Handle unseen categories
            def safe_transform(value):
                try:
                    return encoder.transform([value])[0]
                except ValueError:
                    most_frequent_class = encoder.classes_[0]
                    return encoder.transform([most_frequent_class])[0]
            
            data_processed[col] = data_processed[col].apply(safe_transform)
    
    # Ensure all required features are present
    for feature in components['feature_names']:
        if feature not in data_processed.columns:
            data_processed[feature] = 0
    
    # Select features in correct order
    data_processed = data_processed[components['feature_names']]
    
    # Scale features if needed (Random Forest typically doesn't need scaling)
    if type(components['model']).__name__ in ['LinearRegression', 'Ridge', 'Lasso', 'SVR', 'MLPRegressor']:
        data_processed = components['scaler'].transform(data_processed)
    else:
        data_processed = data_processed.values
    
    # Make prediction
    return components['model'].predict(data_processed)[0]


@api_view(['GET'])
def predict_investment(request, project_id):
    """API endpoint to get investment success prediction for a project"""
    try:
        # Load model components
        components = load_model_components()
        
        # Fetch project data from Firebase
        project_info = db.reference(f'projects/{project_id}').get()
        analysis_info = db.reference(f'analysis/{project_id}').get()
        
        if not project_info or not analysis_info:
            return Response({"error": "Project not found"}, status=404)
        
        # Prepare data for prediction
        prediction_data = prepare_prediction_data(project_info, analysis_info)
        df = pd.DataFrame([prediction_data])
        
        # Make prediction
        success_probability = predict_investment_success(df, components)
        
        # Determine risk level and recommendation
        if success_probability < 0.3:
            risk_level = "High Risk"
            recommendation = "Not Recommended"
            risk_emoji = "🔴"
        elif success_probability < 0.7:
            risk_level = "Medium Risk"
            recommendation = "Consider with Caution"
            risk_emoji = "🟡"
        else:
            risk_level = "Low Risk"
            recommendation = "Recommended Investment"
            risk_emoji = "🟢"
        
        # Prepare key insights based on data
        key_insights = []
        
        # Revenue insights
        revenue = prediction_data['revenue']
        if revenue > 0:
            if revenue > 1000000:
                key_insights.append("Strong revenue performance")
            elif revenue < 100000:
                key_insights.append("Revenue is below market average")
        
        # Growth insights
        if prediction_data['revenue_growth'] > 0.25:
            key_insights.append("Excellent growth trajectory")
        elif prediction_data['revenue_growth'] < 0.05:
            key_insights.append("Growth rate is concerning")
        
        # Customer insights
        if prediction_data['repeat_purchase_rate'] > 0.7:
            key_insights.append("Strong customer retention")
        elif prediction_data['churn_rate'] > 0.3:
            key_insights.append("High churn rate is a risk factor")
        
        # Financial health
        if prediction_data['profit_margin'] > 0.2:
            key_insights.append("Healthy profit margins")
        elif prediction_data['profit_margin'] < 0:
            key_insights.append("Currently operating at a loss")
        
        # Return comprehensive response
        response_data = {
            "project_id": project_id,
            "project_name": project_info.get('projectName', 'Unnamed Project'),
            "prediction": {
                "success_probability": float(success_probability),
                "success_percentage": float(success_probability * 100),
                "risk_level": risk_level,
                "risk_indicator": risk_emoji,
                "recommendation": recommendation
            },
            "key_insights": key_insights,
            "analysis_timestamp": datetime.now().isoformat(),
            "model_info": "Random Forest Regressor (R² score: 0.87)"
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            "error": "Failed to generate prediction",
            "details": str(e)
        }, status=500)
    

# Example usage:
# response = predict_investment(request, 'project123')
# print(response.data)


# Example urlpatterns = [
#     path('api/predict_investment/<str:project_id>/', predict_investment),
# ]
