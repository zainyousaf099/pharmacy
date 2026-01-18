# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.role, name="role"),
    path("doctor-login/", views.doctor_login, name="doctor_login"),
    path("opd-login/", views.opd_login, name="opd_login"),
    path("pharmacy-login/", views.pharmacy_login, name="pharmacy_login"),
    path("logout/", views.logout_staff, name="logout_staff"),
    path("api/verify-menu-password/", views.verify_menu_password, name="verify_menu_password"),
]
