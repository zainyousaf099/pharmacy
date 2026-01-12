from django.urls import path
from . import views

urlpatterns = [
    # Doctor URLs
    path('admit-patient/', views.admit_patient, name='admit_patient'),
    path('doctor/admitted-patients/', views.doctor_admitted_patients_list, name='doctor_admitted_patients_list'),
    
    # OPD Reception URLs
    path('admitted-patients/', views.admitted_patients_list, name='admitted_patients_list'),
    path('assign-room/<int:admission_id>/', views.assign_room_bed, name='assign_room_bed'),
    path('discharge/<int:admission_id>/', views.discharge_patient, name='discharge_patient'),
    # path('discharge-billing/<int:admission_id>/', views.discharge_billing, name='discharge_billing'),  # MOVED TO PHARMACY
    path('add-charge/<int:admission_id>/', views.add_other_charge, name='add_other_charge'),
    
    # API URLs
    path('api/available-beds/', views.get_available_beds, name='get_available_beds'),
    path('api/search-admitted/', views.search_admitted_patient, name='search_admitted_patient'),
]
