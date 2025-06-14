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
    upload_video,
    get_reels,
    upload_national_card,
    send_reset_link,
    reset_password_with_code,
    life_picture, 
    profile_details,
    investment_details,
    set_user_role,
    get_user_data,
    change_password,
    change_email,
    delete_account
)

# Founder app views
from founder.views import (
    insert_project,
    monthly_finance, 
    insert_business_details,
    TransactionsAPI,
    create_project, 
    send_phase3_email,
    founder_home,
    founder_dashboard_overview,
    investment_return_vs_comparison,
    portfolio_performance,
    profit_margin_trend,
    ProductsAPI,
    investor_manager,
    get_revenue_growth,
    add_revenue_entry,
    predict_investment
    )

# Investor app views
from investor.views import (
    interests,
    get_category_percentages,
    get_user_interest_projects,
    SavedProjectsAPI,
    get_dashboard_summary,
    initiate_payment,
    paymob_callback,
    search_projects,
    add_invested_project,
    total_investments,
    get_user_invested_projects,
    roi_vs_saving,
    balance_history,
    investor_profile,
    closing_soon_projects,
    top_raised_projects,
    trending_this_month,
    FinancialReportDetailView,
    FinancialReportView,
    ReportView,
    ReportDetailView,
    TransactionReportView,
    TransactionReportDetailView,
    user_investment_project_details,
)

from web.views import (
    add_monthly_finance,
    get_investment_growth,
    get_my_investments,
    get_investment_distribution,
    portfolio_vs_comparison,
    investor_management
)

from .utils import get_founder_projects

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
    path('password-reset-link/', send_reset_link, name='password-reset-link'),
    path('upload-video/', upload_video, name='upload_video'),
    path('get-reels/', get_reels, name='get_reels'),
    path('send-reset-link/', send_reset_link, name='send_reset_link'),
    path('reset-password/', reset_password_with_code, name='reset-password'),
    path('life-picture/', life_picture, name='life_picture'),
    path('upload-national-card/', upload_national_card, name='upload-national-card'),
    path('account-verificiation/',  profile_details, name='account_verificiation'), 
    path('account-verificiation-2/',  investment_details, name='account_verificiation'), 
    path('role/', set_user_role, name='set_role'),
    path('profile/<str:user_id>/', get_user_data, name='profile'),
    path('change-password/', change_password, name='set_role'),
    path('change-email/', change_email, name='set_role'),
    path('delete-account/', delete_account, name='set_role'),


    # Investor endpoints
    path('interests/', interests, name='interests'),
    path('welcome/<str:user_id>/', investor_profile, name='welcome'),
    path('interest-projects/<str:user_id>/', get_user_interest_projects, name='get_user_interest_projects'),
    path('closing-soon/', closing_soon_projects, name='closing_soon_projects'),
    path('top-raised/', top_raised_projects, name='top_raised_projects'),
    path('trending/', trending_this_month, name='trending_this_month'),
    path('save-project/', SavedProjectsAPI.as_view(), name='save_project'),
    path('saved-projects/<str:user_id>/', SavedProjectsAPI.as_view(), name='get_saved_projects'),
    path('delete-saved-project/<str:user_id>/<str:saved_id>/', SavedProjectsAPI.as_view(), name='delete_saved_project'),
    path('dashboard/overview/<str:user_id>/', get_dashboard_summary, name='get_dashboard_summary'),
    path('get-category-percentages/', get_category_percentages, name='get_category_percentages'),
    path('initiate-payment/', initiate_payment, name='initiate_payment'),
    path('paymob-callback/', paymob_callback, name='paymob_callback'),
    path('search/', search_projects, name='search'),
    path('add-invested-project/', add_invested_project, name='add_invested_project'), # dump data
    path('dashboard/total-investments/<str:user_id>/', total_investments, name='add_invested_project'),
    path('dashboard/invested-projects/<str:user_id>/', get_user_invested_projects, name='get_user_invested_project'),
    path('dashboard/roi-vs-saving/<str:user_id>/', roi_vs_saving, name="roi_vs_saving"),
    path('dashboard/balance-history/<str:user_id>/', balance_history, name="balance_history"),
    path('invested-projects/<str:user_id>/<str:investments_id>/', user_investment_project_details, name='get_investment_distribution'),
    path('investor/<str:user_id>/financial-reports/', FinancialReportView.as_view(), name='financial-report'),
    path('investor/financial-reports/<str:report_id>/', FinancialReportDetailView.as_view(), name='financial-report-detail'),
    path('investor/transaction-reports/<str:user_id>/', TransactionReportView.as_view(), name='transaction-reports'),
    path('investor/transaction-reports/<str:report_id>/detail/', TransactionReportDetailView.as_view(), name='transaction-report-detail'),
    path('investor/reports/<str:report_id>/detail/',ReportDetailView.as_view(), name='report-detail'),
    path('investor/reports/<str:user_id>/', ReportView.as_view(), name='reports'),


    # Founder endpoints
    path('insert-project/', insert_project, name='insert_project'),
    path('insert-business-details/', insert_business_details, name='insert_business_details'),
    path('create-project/', create_project, name='create_project'),
    path('founder/transactions/<str:user_id>/', TransactionsAPI.as_view(), name="transactions_api"),
    path('founder/products/', ProductsAPI.as_view(), name="add_product"),
    path('email/', send_phase3_email, name='email'),
    path('founder-home/<str:project_id>', founder_home, name='founder_home'),
    path('founder/dashboard/overview/<str:user_id>/', founder_dashboard_overview, name='founder_dashboard_overview'), # flutter, web
    path('founder/dashboard/return-vs-comparison/<str:user_id>/', investment_return_vs_comparison, name='investment_return_vs_comparison'), # flutter, web
    path('founder/dashboard/portfolio-performance/<str:user_id>/', portfolio_performance, name='portfolio_performance'), # flutter only 
    path('founder/dashboard/profit-margin-trend/<str:user_id>/', profit_margin_trend, name='profit_margin_trend'), # flutter, web
    path('founder/dashboard/monthly-finance/<str:user_id>/', monthly_finance, name='monthly-finance'),
    path('founder/dashboard/investor-manager/<str:user_id>/', investor_manager, name='investor_manager'),
    path('founder/dashboard/revenue-growth/<str:user_id>/', get_revenue_growth, name='get_revenue_growth'),
    path('founder/dashboard/revenue-entries/create/', add_revenue_entry, name='add_revenue_entry'),

    # Web endpoints
    #path('add-finance/', add_monthly_finance, name='add_monthly_finance'),
    path('add_monthly_finance/', add_monthly_finance, name='add_monthly_finance'),
    path('dashboard/growth/<str:user_id>/', get_investment_growth, name='get_investment_growth'),
    path('dashboard/investments/<str:user_id>/',get_my_investments, name='get_my_investments'),
    path('dashboard/distribution/<str:user_id>/', get_investment_distribution, name='get_investment_distribution'),
    path('web/founder/dashboard/portfolio-vs-comparison/<str:user_id>/', portfolio_vs_comparison, name='portfolio_vs_comparison'),
    path('web/founder/investor-managment/<str:user_id>/', investor_management, name='investor_management'),
    

    path('api/predict_investment/<str:project_id>/', predict_investment),   
    
    # Swagger documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    
    path('healthz', health_check),
    

    ]

