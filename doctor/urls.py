from django.urls import path
from . import views

urlpatterns = [
    path('', views.doctor_panel, name='doctor_panel'),
    path('api/search-medicines/', views.search_medicines_api, name='search_medicines_api'),
    path('api/search-patient/', views.search_patient, name='search_patient'),
    path('print-prescription/<str:patient_ref_no>/', views.print_prescription, name='print_prescription'),
]
