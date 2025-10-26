from django.shortcuts import render

# Create your views here.
def doctor_panel(request):
    
    return render(request,'doctortemp/dashboard.html')