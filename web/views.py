from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from firebase_admin import db
from rest_framework import status



@api_view(['GET'])
def monthly_finance_firebase_view(request):
    ref = db.reference('monthly_finance')
    data = ref.get()

    formatted_data = []
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


@api_view(['POST'])
def add_monthly_finance(request):
    data = request.data
    month = data.get('month')
    revenue = data.get('revenue')
    loss = data.get('loss')

    if not all([month, revenue is not None, loss is not None]):
        return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

    month = month.capitalize()

    ref = db.reference(f'monthly_finance/{month}')
    ref.set({
        'revenue': revenue,
        'loss': loss
    })

    return Response({"message": f"{month} data saved successfully"}, status=status.HTTP_201_CREATED)


# 1. Get Dashboard Summary (top cards)
@api_view(['GET'])
def get_dashboard_summary(request, user_id):
    investments_ref = db.reference(f'users/{user_id}/investments')
    data = investments_ref.get() or {}

    total_investment = 0
    total_profit = 0
    investment_types = set()
    businesses = []

    for business_id, inv in data.items():
        total_investment += inv.get('amount', 0)
        total_profit += inv.get('net_profit', 0)
        investment_types.add(inv.get('type', ''))
        businesses.append(inv.get('business_name', ''))

    return Response({
        "total_investment": total_investment,
        "net_profit": total_profit,
        "investment_types": list(investment_types),
        "businesses_invested_in": businesses
    })


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


# 3. Get My Investments (list)
@api_view(['GET'])
def get_my_investments(request, user_id):
    investments_ref = db.reference(f'users/{user_id}/investments')
    data = investments_ref.get() or {}

    response = []
    for business_id, inv in data.items():
        response.append({
            "name": inv.get('business_name'),
            "amount": inv.get('amount'),
            "roi": inv.get('roi', 0)
        })

    return Response(response)


# 4. Get Investment Distribution (pie chart)
@api_view(['GET'])
def get_investment_distribution(request, user_id):
    investments_ref = db.reference(f'users/{user_id}/investments')
    data = investments_ref.get() or {}

    total = sum([inv.get('amount', 0) for inv in data.values()])
    distribution = []

    for business_id, inv in data.items():
        percent = (inv.get('amount', 0) / total * 100) if total > 0 else 0
        distribution.append({
            "label": inv.get("business_name"),
            "value": round(percent, 1)
        })

    return Response(distribution)
