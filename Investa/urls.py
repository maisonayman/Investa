"""
URL configuration for Investa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from user.views import request_otp,verify_otp,personal_data_detail,personal_data_list,sign_in,process_payment
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('request-otp/', request_otp, name='request_otp'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('personal_data_list/', personal_data_list, name='personal_data_list'),
    path('personal_data_detail/', personal_data_detail, name='personal_data_detail'),
    path('personal_data_detail/<str:national_id>/', personal_data_detail, name='personal_data_detail'),
    path('sign_in/', sign_in, name='sign_in'),
    path('process_payment/', process_payment, name='process_payment'),
    

]
