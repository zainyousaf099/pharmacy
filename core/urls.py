
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('accounts.urls')),
    path('opd/',include('opd.urls')),
    path('doctor/',include('doctor.urls')),
    path('pharmacy/',include('pharmacy.urls')),
    path('inventory/',include('inventory.urls')),
]
