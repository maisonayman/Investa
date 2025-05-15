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

# User app views
from user.views import (
    request_otp,
    verify_otp,
    personal_data_detail,
    personal_data_list,
    sign_in,
    #submit_review,
    #request_password_reset,
    #upload_video,
    #get_reels
)

# Founder app views
from founder.views import create_project

# Investor app views
from investor.views import (
    interests,
    #get_category_percentages,
    #get_total_investments,
    process_payment,
    get_user_interest_projects,
    get_other_projects
)

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
    path('personal_data_list/', personal_data_list, name='personal_data_list'),
    path('personal_data_detail/<str:national_id>/', personal_data_detail, name='personal_data_detail'),
    path('sign_in/', sign_in, name='sign_in'),
    #path('submit_review/', submit_review, name='submit_review'),
    #path('request_password_reset/', request_password_reset, name='request_password_reset'),
    #path('upload_video/', upload_video, name='upload_video'),
    #path('get_reels/', get_reels, name='get_reels'),

    # Founder endpoints
    path('create_project/', create_project, name='create_project'),

    # Investor endpoints
    path('interests/', interests, name='interests'),
    path('get_other_projects/', get_other_projects, name='get_other_projects'),
    path('interest_projects/', get_user_interest_projects, name='get_user_interest_projects'),
    #path('get_category_percentages/<str:national_id>/', get_category_percentages, name='get_category_percentages'),
    #path('get_total_investments/<str:national_id>/', get_total_investments, name='get_total_investments'),
    path('process_payment/', process_payment, name='process_payment'),

    # Swagger documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
