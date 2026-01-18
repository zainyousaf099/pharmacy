
from django.urls import path
from . import views

urlpatterns = [
    path('', views.pharmacypanel, name='pharmacypanel'),
    path('api/search-patient/', views.search_patient_prescription, name='search_patient_prescription'),
    path('api/search-medicines/', views.search_medicines_for_pharmacy, name='search_medicines_for_pharmacy'),
    path('api/process-order/', views.process_pharmacy_order, name='process_pharmacy_order'),
    
    # Pharmacy Queue API
    path('api/queue/', views.pharmacy_queue_api, name='pharmacy_queue_api'),
    path('api/queue/select/<int:patient_id>/', views.pharmacy_queue_select, name='pharmacy_queue_select'),
    path('api/queue/complete/<int:patient_id>/', views.pharmacy_queue_complete, name='pharmacy_queue_complete'),
    
    # Admitted patients
    path('admitted-patients/', views.admitted_patients_pharmacy, name='admitted_patients_pharmacy'),
    path('dispense-admitted/', views.dispense_to_admitted, name='dispense_to_admitted'),
    path('discharge-billing/<int:admission_id>/', views.discharge_billing_pharmacy, name='discharge_billing_pharmacy'),
    
    # Medicine Return System
    path('api/return/search-bill/', views.search_bill_for_return, name='search_bill_for_return'),
    path('api/return/process/', views.process_medicine_return, name='process_medicine_return'),
    path('api/return/history/', views.get_return_history, name='get_return_history'),
    path('api/return/search-medicine/', views.search_medicine_for_return, name='search_medicine_for_return'),
    
    # Database backup & restore
    path('api/download-database/', views.download_database, name='download_database'),
    path('api/upload-database/', views.upload_database, name='upload_database'),
    path('api/database-info/', views.get_database_info, name='get_database_info'),
    
    # Google Drive Cloud Backup
    path('api/gdrive/status/', views.gdrive_status, name='gdrive_status'),
    path('api/gdrive/setup/', views.gdrive_setup, name='gdrive_setup'),
    path('api/gdrive/auth-url/', views.gdrive_auth_url, name='gdrive_auth_url'),
    path('api/gdrive/auth-complete/', views.gdrive_auth_complete, name='gdrive_auth_complete'),
    path('api/gdrive/backup/', views.gdrive_backup, name='gdrive_backup'),
    path('api/gdrive/list-backups/', views.gdrive_list_backups, name='gdrive_list_backups'),
    path('api/gdrive/disconnect/', views.gdrive_disconnect, name='gdrive_disconnect'),
    path('api/gdrive/check-daily/', views.check_daily_backup, name='check_daily_backup'),
    
    # Network/Server API endpoints
    path('api/network/status/', views.network_status, name='network_status'),
    path('api/network/set-server/', views.set_as_server, name='set_as_server'),
    path('api/network/connect/', views.connect_to_server, name='connect_to_server'),
    path('api/network/disconnect/', views.disconnect_from_server, name='disconnect_from_server'),
    path('api/network/ping/', views.server_ping, name='server_ping'),
]
