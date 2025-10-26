# reception/forms.py
from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'phone', 'temperature', 'age', 'weight', 'height']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'patient name',
                'class': 'form-control',
                'style': 'margin-top:10px; padding:8px; width:40%;'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'phone no',
                'class': 'form-control',
                'style': 'margin-top:10px; padding:8px; width:40%;'
            }),
            'age': forms.NumberInput(attrs={
                'placeholder': 'patient age',
                'class': 'form-control',
                'style': 'margin-top:10px; padding:8px; width:40%;'
            }),
            'temperature': forms.NumberInput(attrs={
                'placeholder': 'temperature',
                'class': 'form-control',
                'style': 'margin-top:10px; padding:8px; width:40%;'
            }),
            'weight': forms.NumberInput(attrs={
                'placeholder': 'patient weight',
                'class': 'form-control',
                'style': 'margin-top:10px; padding:8px; width:40%;'
            }),
            'height': forms.NumberInput(attrs={
                'placeholder': 'patient height',
                'class': 'form-control',
                'style': 'margin-top:10px; padding:8px; width:40%;'
            }),
        }

