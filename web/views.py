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
