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
from django.http import JsonResponse


# User app views
from user.views import (
    request_otp,
    verify_otp,
    PersonalDataList,
    PersonalDataDetail,
    sign_in,
    #submit_review,
    #request_password_reset,
    upload_video,
    get_reels,
    upload_national_card,
    send_reset_link,
    reset_password_with_code,
    life_picture, 
    profile_details,
    investment_details
)

# Founder app views
from founder.views import (
    insert_project,
    insert_business_details,
    TransactionsAPI,
    add_product,
    create_project, 
    send_phase3_email,
    founder_home,
    founder_dashboard_overview,
    investment_return_vs_comparison,
    portfolio_performance,
    profit_margin_trend
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
    get_dashboard_summary,
    initiate_payment,
    paymob_callback,
    search_projects,
    add_invested_project,
    get_user_invested_projects,
    roi_vs_saving,
    balance_history,
    get_user_profile,
    closing_soon_projects,
    top_raised_projects,
    trending_this_month
)

from web.views import (
    monthly_finance_firebase_view, 
    add_monthly_finance,
    get_investment_growth,
    get_my_investments,
    get_investment_distribution
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

def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('admin/', admin.site.urls),

    # User endpoints
    path('request-otp/', request_otp, name='request_otp'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('personal-data/', PersonalDataList.as_view(), name='personal-data-list'),
    path('personal-data/<str:user_id>/', PersonalDataDetail.as_view(), name='personal-data-detail'),
    path('sign-in/', sign_in, name='sign_in'),
    #path('submit_review/', submit_review, name='submit_review'),
    #path('request_password_reset/', request_password_reset, name='request_password_reset'),
    path('upload-video/', upload_video, name='upload_video'),
    path('get-reels/', get_reels, name='get_reels'),
    path('send-reset-link/', send_reset_link, name='send_reset_link'),
    path('reset-password/', reset_password_with_code, name='reset-password'),
    path('life-picture/', life_picture, name='life_picture'),
    path('upload-national-card/', upload_national_card, name='upload-national-card'),
    path('account-verificiation/',  profile_details, name='account_verificiation'), 
    path('account-verificiation-2/',  investment_details, name='account_verificiation'), 


    # Founder endpoints
    path('insert-project/', insert_project, name='insert_project'),
    path('insert-business-details/', insert_business_details, name='insert_business_details'),
    path('create-project/', create_project, name='create_project'),
    path('transactions/', TransactionsAPI.as_view(), name="transactions_api"),
    path('add-product/', add_product, name="add_product"),
    path('email/', send_phase3_email, name='email'),
    path('founder-home/<str:project_id>', founder_home, name='founder_home'),
    path('founder/dashboard/overview/<str:user_id>/', founder_dashboard_overview, name='founder_dashboard_overview'),
    path('founder/dashboard/return-vs-comparison/<str:user_id>/', investment_return_vs_comparison, name='investment_return_vs_comparison'),
    path('founder/dashboard/portfolio-performance/<str:user_id>/', portfolio_performance, name='portfolio_performance'),
    path('founder/dashboard/profit-margin-trend/<str:user_id>/', profit_margin_trend, name='profit_margin_trend'),


    # Investor endpoints
    path('interests/', interests, name='interests'),
    #path('get_other_projects/', get_other_projects, name='get_other_projects'),
    path('welcome/', get_user_profile, name='welcome'),
    path('interest-projects/', get_user_interest_projects, name='get_user_interest_projects'),
    path('closing-soon/', closing_soon_projects, name='closing_soon_projects'),
    path('top-raised/', top_raised_projects, name='top_raised_projects'),
    path('trending/', trending_this_month, name='trending_this_month'),
    path('save-project/', save_project, name='save_project'),
    path('get-saved-projects/<str:user_id>/', get_saved_projects, name='get_saved_projects'),
    path('delete-saved-project/<str:user_id>/<str:saved_id>/', delete_saved_project, name='delete_saved_project'),
    path('dashboard/overview/<str:user_id>/', get_dashboard_summary, name='get_dashboard_summary'),
    path('get-category-percentages/', get_category_percentages, name='get_category_percentages'),
    path('initiate-payment/', initiate_payment, name='initiate_payment'),
    path('paymob-callback/', paymob_callback, name='paymob_callback'),
    path('search/', search_projects, name='search'),
    path('add-invested-project/', add_invested_project, name='add_invested_project'),
    path('dashboard/invested-projects/<str:user_id>/', get_user_invested_projects, name='get_user_invested_project'),
    path('roi_vs_saving/', roi_vs_saving, name="roi_vs_saving"),
    path('balance_history/', balance_history, name="balance_history"),
    path('dashboard/<str:user_id>/growth/', get_investment_growth, name='get_investment_growth'),
    path('dashboard/<str:user_id>/investments/',get_my_investments, name='get_my_investments'),
    path('dashboard/<str:user_id>/distribution/', get_investment_distribution, name='get_investment_distribution'),

    # Web endpoints
    path('monthly-finance/', monthly_finance_firebase_view, name='monthly-finance'),
    path('add-finance/', add_monthly_finance, name='add_monthly_finance'),
    
    # Swagger documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),


    path('healthz', health_check),
    
]

