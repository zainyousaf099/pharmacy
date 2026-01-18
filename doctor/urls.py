from django.urls import path
from . import views

urlpatterns = [
    path('', views.doctor_panel, name='doctor_panel'),
    path('api/search-medicines/', views.search_medicines_api, name='search_medicines_api'),
    path('api/search-patient/', views.search_patient, name='search_patient'),
    path('api/patient-prescriptions/', views.get_patient_prescriptions_api, name='get_patient_prescriptions_api'),
    path('print-prescription/<str:patient_ref_no>/', views.print_prescription, name='print_prescription'),
    
    # Patient Statistics
    path('patients/', views.patient_statistics, name='patient_statistics'),
    path('api/patient-stats/', views.patient_statistics_api, name='patient_statistics_api'),
    path('api/patient-detail/<str:ref_no>/', views.patient_detail_api, name='patient_detail_api'),
    
    # Patient Queue System
    path('api/patient-queue/', views.get_patient_queue, name='get_patient_queue'),
    path('api/select-patient/', views.select_patient_from_queue, name='select_patient_from_queue'),
    path('api/mark-checked/', views.mark_patient_checked, name='mark_patient_checked'),
    
    # Template Management URLs
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<uuid:template_id>/', views.template_detail, name='template_detail'),
    path('templates/<uuid:template_id>/delete/', views.template_delete, name='template_delete'),
    path('templates/<uuid:template_id>/add-medicine/', views.template_add_medicine, name='template_add_medicine'),
    path('templates/<uuid:template_id>/remove-medicine/<uuid:medicine_id>/', views.template_remove_medicine, name='template_remove_medicine'),
    path('templates/<uuid:template_id>/update-sections/', views.template_update_sections, name='template_update_sections'),
    
    # Template API endpoints
    path('api/templates/', views.get_all_templates_api, name='get_all_templates_api'),
    path('api/templates/<uuid:template_id>/medicines/', views.get_template_medicines_api, name='get_template_medicines_api'),
]
