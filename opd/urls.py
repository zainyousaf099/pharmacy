# reception/urls.py
from django.urls import path
from . import views



urlpatterns = [
    path('', views.opdpanel, name='opdpanel'),
    path('reception/', views.opdpanel, name='reception_panel'),
    path('patient/<str:ref_no>/', views.patient_detail, name='patient_detail'),
    path('admit_patient/', views.admit_patient ,name='admit_patient'),
    path('print-receipt/<int:patient_id>/', views.print_patient_receipt, name='print_patient_receipt'),
]
