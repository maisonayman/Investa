from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from firebase_admin import db
from rest_framework import status
from datetime import datetime
from collections import defaultdict
import calendar
from Investa.utils import get_founder_projects
from rest_framework.views import APIView


@api_view(['POST'])
def add_monthly_finance(request):
    data = request.data
    user_id = data.get('user_id')
    month = data.get('month')
    revenue = data.get('revenue')
    loss = data.get('loss')

    if not all([user_id, month, revenue is not None, loss is not None]):
        return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

    month = month.capitalize()

    ref = db.reference(f'users/{user_id}/monthly_finance/{month}')
    ref.set({
        'revenue': revenue,
        'loss': loss
    })

    return Response({"message": f"{month} data saved successfully for user {user_id}"}, status=status.HTTP_201_CREATED)


# 2. Get Investment Growth (line chart)
@api_view(['GET'])
def get_investment_growth(request, user_id):
    analytics_ref = db.reference(f'analytics/{user_id}/growth')
    data = analytics_ref.get() or {}

    # Format: {"Jan": {"investment_value": 100000, "net_profit": 25000}, ...}
    months = []
    investment_values = []
    net_profits = []

    for month in ['Jan', 'Feb', 'Mar', 'Apr']:
        month_data = data.get(month, {})
        months.append(month)
        investment_values.append(month_data.get("investment_value", 0))
        net_profits.append(month_data.get("net_profit", 0))

    return Response({
        "months": months,
        "investment_values": investment_values,
        "net_profits": net_profits
    })


@api_view(['GET'])
def get_my_investments(request, user_id):
    try:
        investments_ref = db.reference(f'users/{user_id}/investments')
        user_investments = investments_ref.get() or {}

        projects_ref = db.reference('projects')
        all_projects = projects_ref.get() or {}

        response = []
        for inv_id, inv in user_investments.items():
            project_id = inv.get('project_id')
            project_name = all_projects.get(project_id, {}).get('projectName', 'Unknown Project')

            response.append({
                "name": project_name,
                "amount": inv.get('invested_amount', 0),
                "roi": inv.get('roi', 0)
            })

        return Response(response, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)



@api_view(['GET'])
def get_investment_distribution(request, user_id):
    investments_ref = db.reference(f'users/{user_id}/investments')
    user_investments = investments_ref.get() or {}

    if not user_investments:
        return Response([], status=status.HTTP_200_OK)

    projects_ref = db.reference('projects')
    all_projects = projects_ref.get() or {}

    # ✅ احسب التوتال
    total = sum([float(inv.get('invested_amount', 0)) for inv in user_investments.values()])

    distribution = []

    for inv in user_investments.values():
        project_id = inv.get("project_id")
        invested_amount = float(inv.get("invested_amount", 0))

        # ✅ هات اسم المشروع من projects
        project_data = all_projects.get(project_id, {})
        project_name = project_data.get("projectName", "Unknown Project")

        # ✅ احسب النسبة
        percent = (invested_amount / total * 100) if total > 0 else 0

        distribution.append({
            "label": project_name,
            "value": round(percent, 1)
        })

    return Response(distribution)



@api_view(['GET'])
def portfolio_vs_comparison(request, user_id):
    projects_ref = db.reference('projects')
    all_projects = projects_ref.get() or {}

    founder_project_ids = [
        pid for pid, proj in all_projects.items()
        if proj.get('user_id', '').strip() == user_id.strip()
    ]

    invested_ref = db.reference('invested_projects')
    investments = invested_ref.get() or {}

    performance = defaultdict(float)
    comparison = defaultdict(float)

    for inv in investments.values():
        if inv.get('project_id') in founder_project_ids:
            date_str = inv.get("invested_at", "")
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                month_label = date_obj.strftime('%b')
            except:
                continue

            roi = float(inv.get('roi', 0))
            performance[month_label] += roi
            comparison[month_label] += roi * 0.9  # 👈 مقارنة تعتمد على ROI

    sorted_months = sorted(performance.keys(), key=lambda m: datetime.strptime(m, "%b").month)
    performance_data = [performance[m] for m in sorted_months]
    comparison_data = [comparison[m] for m in sorted_months]

    return Response({
        "dates": sorted_months,
        "portfolio_performance": performance_data,
        "comparison_data": comparison_data
    })


@api_view(['GET'])
def investor_management(request, user_id):
    founder_projects = get_founder_projects(user_id)
    founder_project_ids = [proj.get("project_id") for proj in founder_projects]

    inv_ref = db.reference("invested_projects")
    all_investments = inv_ref.get()

    investors_map = {}

    if all_investments:
        for inv_id, inv in all_investments.items():
            if inv.get("project_id") in founder_project_ids:
                investor_id = inv.get("user_id")
                user_ref = db.reference(f"users/{investor_id}")
                user_data = user_ref.get() or {}

                username = user_data.get("username", "Unknown")
                email = user_data.get("email", "Unknown")

                invested_amount = float(inv.get("invested_amount", 0))
                roi = float(inv.get("roi", 0))
                date_str = inv.get("invested_at", "")
                status = inv.get("status", "Unknown")

                # Format date to only include yyyy-mm-dd
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
                except:
                    date = date_str

                key = f"{username}_{email}"  # to prevent duplicates

                if key in investors_map:
                    investors_map[key]["invested_amount"] += invested_amount
                    investors_map[key]["roi"] += roi
                    if date > investors_map[key]["invested_at"]:
                        investors_map[key]["invested_at"] = date
                    investors_map[key]["status"] = status
                else:
                    investors_map[key] = {
                        "username": username,
                        "email": email,
                        "invested_amount": invested_amount,
                        "roi": roi,
                        "reinsurance": "N/A",  # Change if available
                        "invested_at": date,
                        "investor_share": "N/A",  # Add logic if you calculate it
                        "status": status
                    }

    return Response({"investors": list(investors_map.values())})



class DailyTransactionsAPI(APIView):
    def post(self, request, user_id):
        try:
            data = request.data
            required_fields = ['date', 'type', 'description', 'amount', 'payment_method', 'responsible']

            missing = [field for field in required_fields if field not in data]
            if missing:
                return Response({"error": f"Missing fields: {', '.join(missing)}"}, status=status.HTTP_400_BAD_REQUEST)

            ref = db.reference(f'users/{user_id}/daily_transactions')
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
        
    def get(self, request, user_id):
        ref = db.reference(f'users/{user_id}/daily_transactions')
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
        