from django.shortcuts import render

# Create your views here.
def pharmacypanel(request):
    
    return render(request,'pharmacytemp/dashboard.html')