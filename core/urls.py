
from django.contrib import admin
from django.urls import path,include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('accounts.urls')),
    path('opd/',include('opd.urls')),
    path('doctor/',include('doctor.urls')),
    path('pharmacy/',include('pharmacy.urls')),
    path('inventory/',include('inventory.urls')),
    
    # Modal System Demo
    path('modal-demo/', TemplateView.as_view(template_name='modal_demo.html'), name='modal_demo'),
]

