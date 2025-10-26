from django.urls import path
from . import views

urlpatterns = [
    path('',views.doctor_panel,name='doctor_panel'),
]
