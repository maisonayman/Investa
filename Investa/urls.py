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
from django.urls import path, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from investor import views 

# User app views
from user.views import (
    request_otp,
    verify_otp,
    personal_data_detail,
    personal_data_list,
    sign_in,
    #submit_review,
    #request_password_reset,
    upload_video,
    get_reels,
    upload_national_card,
    send_reset_link,
    reset_password_with_code,
    life_picture,
    get_user_profile
)

# Founder app views
from founder.views import (
    insert_project,
    insert_business_details,
    search_projects
)

# Investor app views
from investor.views import (
    interests,
    get_category_percentages,
    get_user_interest_projects,
    #get_other_projects,
    save_project,
    get_saved_projects,
    delete_saved_project,
    total_investment,
    total_current_net_profit,
    investment_types,
    businesses_invested_in,
    initiate_payment,
    paymob_callback
)

from web.views import monthly_finance_firebase_view, add_monthly_finance

# Swagger schema setup
schema_view = get_schema_view(
   openapi.Info(
      title="Your API",
      default_version='v1',
      description="API documentation",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # User endpoints
    path('request-otp/', request_otp, name='request_otp'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('personal-data-list/', personal_data_list, name='personal_data_list'),
    path('personal-data-detail/<str:user_id>/', personal_data_detail, name='personal_data_detail'),
    path('sign-in/', sign_in, name='sign_in'),
    path('user-profile/<str:user_id>/', get_user_profile, name='get_user_profile'),
    #path('submit_review/', submit_review, name='submit_review'),
    #path('request_password_reset/', request_password_reset, name='request_password_reset'),
    path('upload-video/', upload_video, name='upload_video'),
    path('get-reels/', get_reels, name='get_reels'),
    path('send-reset-link/', send_reset_link, name='send_reset_link'),
    path('reset-password/', reset_password_with_code, name='reset-password'),
    path('life-picture/', life_picture, name='life_picture'),
    path('upload-national-card/', upload_national_card, name='upload-national-card'), 

 
    # Founder endpoints
    path('insert-project/', insert_project, name='insert_project'),
    path('insert-business_details/', insert_business_details, name='insert_business_details'),
    path('search-projects/', search_projects, name='search_projects'),


    # Investor endpoints
    path('interests/', interests, name='interests'),
    #path('get_other_projects/', get_other_projects, name='get_other_projects'),
    path('interest-projects/', get_user_interest_projects, name='get_user_interest_projects'),
    path('save-project/', save_project, name='save_project'),
    path('get-saved-projects/<str:user_id>/', get_saved_projects, name='get_saved_projects'),
    path('delete-saved-project/<str:user_id>/<str:saved_id>/', delete_saved_project, name='delete_saved_project'),
    path('net-profit/', total_current_net_profit, name='total_current_net_profit'),
    path('investment-types/',investment_types, name='investment_types'),
    path('businesses-invested/',businesses_invested_in , name='businesses_invested_in' ),
    path('total-investment/',total_investment , name='total_investment' ),
    path('get-category-percentages/<str:user_id>/', get_category_percentages, name='get_category_percentages'),
    path('initiate-payment/', initiate_payment, name='initiate_payment'),
    path('paymob-callback/', paymob_callback, name='paymob_callback'),


    # Web endpoints
    path('monthly-finance/', monthly_finance_firebase_view, name='monthly-finance'),
    path('add-finance/', add_monthly_finance, name='add_monthly_finance'),

    # Swagger documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),



]
