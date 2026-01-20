# inventory/urls.py
from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("products/", views.product_list, name="product_list"),
    path("product/add/", views.product_create, name="product_create"),
    path("product/<uuid:pk>/", views.product_detail, name="product_detail"),
    path("product/<uuid:pk>/edit/", views.product_update, name="product_update"),
    path("product/<uuid:pk>/purchase/", views.add_purchase, name="product_purchase"),
    path("product/<uuid:pk>/sale/", views.add_sale, name="product_sale"),
    path("product/<uuid:pk>/add-batch/", views.add_batch, name="add_batch"),
    
    # Batch Management
    path("batches/", views.batch_list, name="batch_list"),
    path("batch/<uuid:pk>/", views.batch_detail, name="batch_detail"),
    
    # Distributor Management
    path("distributors/", views.distributor_list, name="distributor_list"),
    path("distributor/add/", views.distributor_create, name="distributor_create"),
    path("distributor/<uuid:pk>/", views.distributor_detail, name="distributor_detail"),
    path("distributor/<uuid:pk>/edit/", views.distributor_edit, name="distributor_edit"),
    path("distributor/<uuid:pk>/payment/", views.distributor_add_payment, name="distributor_add_payment"),
    path("distributor/<uuid:pk>/purchase/", views.distributor_add_purchase, name="distributor_add_purchase"),
    path("distributor-dues/", views.distributor_dues_report, name="distributor_dues_report"),
    path("api/distributors/", views.distributor_api, name="distributor_api"),
    
    path("reports/", views.reports, name="reports"),
    path("reports/csv/", views.reports_csv, name="reports_csv"),
    path("reports/pdf/", views.reports_pdf, name="reports_pdf"),
    path("expenses/", views.expense_list, name="expense_list"),
    path("expenses/reports/", views.expense_reports, name="expense_reports"),
    path("expenses/reports/csv/", views.expense_reports_csv, name="expense_reports_csv"),
    path("expenses/reports/pdf/", views.expense_reports_pdf, name="expense_reports_pdf"),
    path("expenses/add/", views.expense_create, name="expense_create"),
    path("api/search-products/", views.search_products_api, name="search_products_api"),
    path("api/product/<uuid:product_id>/", views.product_detail_api, name="product_detail_api"),
    
    # Comprehensive Reports
    path("all-reports/", views.all_reports, name="all_reports"),
    path("medicine-report/<uuid:pk>/", views.medicine_report, name="medicine_report"),
    path("medicine-report/<uuid:pk>/pdf/", views.medicine_report_pdf, name="medicine_report_pdf"),
    path("stock-report/", views.stock_report, name="stock_report"),
    path("stock-report/pdf/", views.stock_report_pdf, name="stock_report_pdf"),
    path("low-stock-report/", views.low_stock_report, name="low_stock_report"),
    path("low-stock-report/pdf/", views.low_stock_report_pdf, name="low_stock_report_pdf"),
    path("expiry-report/", views.expiry_report, name="expiry_report"),
    path("expiry-report/pdf/", views.expiry_report_pdf, name="expiry_report_pdf"),
    path("distributor-report/", views.distributor_report, name="distributor_report"),
    path("distributor-report/pdf/", views.distributor_report_pdf, name="distributor_report_pdf"),
    path("category-report/", views.category_report, name="category_report"),
    path("category-report/pdf/", views.category_report_pdf, name="category_report_pdf"),
    path("sales-analysis/", views.sales_analysis_report, name="sales_analysis_report"),
    path("sales-analysis/pdf/", views.sales_analysis_report_pdf, name="sales_analysis_report_pdf"),
    path("profit-loss/", views.profit_loss_report, name="profit_loss_report"),
    path("profit-loss/pdf/", views.profit_loss_report_pdf, name="profit_loss_report_pdf"),
]
