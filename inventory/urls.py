# inventory/urls.py
from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("product/add/", views.product_create, name="product_create"),
    path("product/<uuid:pk>/", views.product_detail, name="product_detail"),
    path("product/<uuid:pk>/purchase/", views.add_purchase, name="product_purchase"),
]
