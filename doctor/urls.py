from django.urls import path
from . import views

urlpatterns = [
    path('', views.doctor_panel, name='doctor_panel'),
    path('api/search-medicines/', views.search_medicines_api, name='search_medicines_api'),
    path('api/search-patient/', views.search_patient, name='search_patient'),
    path('print-prescription/<str:patient_ref_no>/', views.print_prescription, name='print_prescription'),
    
    # Template Management URLs
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<uuid:template_id>/', views.template_detail, name='template_detail'),
    path('templates/<uuid:template_id>/delete/', views.template_delete, name='template_delete'),
    
    # Template API endpoints
    path('api/templates/', views.get_all_templates_api, name='get_all_templates_api'),
    path('api/templates/<uuid:template_id>/medicines/', views.get_template_medicines_api, name='get_template_medicines_api'),
]
