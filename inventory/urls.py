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
    path("reports/", views.reports, name="reports"),
    path("expenses/", views.expense_list, name="expense_list"),
    path("expenses/add/", views.expense_create, name="expense_create"),
    path("api/search-products/", views.search_products_api, name="search_products_api"),
]
