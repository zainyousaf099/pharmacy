
from django.urls import path
from . import views

urlpatterns = [
    path('', views.pharmacypanel, name='pharmacypanel'),
    path('api/search-patient/', views.search_patient_prescription, name='search_patient_prescription'),
    path('api/process-order/', views.process_pharmacy_order, name='process_pharmacy_order'),
]
