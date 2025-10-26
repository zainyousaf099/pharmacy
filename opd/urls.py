# reception/urls.py
from django.urls import path
from . import views



urlpatterns = [
    path('', views.opdpanel, name='opdpanel'),
    path('patient/<str:ref_no>/', views.patient_detail, name='patient_detail'),
    path('admit_patient/', views.admit_patient ,name='admit_patient')
]
