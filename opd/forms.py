# reception/forms.py
from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'phone', 'temperature', 'age_years', 'age_months', 'age_days', 'weight', 'height']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'patient name',
                'class': 'form-control',
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'phone no',
                'class': 'form-control',
            }),
            'age_years': forms.NumberInput(attrs={
                'placeholder': 'years',
                'class': 'form-control',
                'min': '0',
                'max': '120',
            }),
            'age_months': forms.NumberInput(attrs={
                'placeholder': 'months',
                'class': 'form-control',
                'min': '0',
                'max': '11',
            }),
            'age_days': forms.NumberInput(attrs={
                'placeholder': 'days',
                'class': 'form-control',
                'min': '0',
                'max': '30',
            }),
            'temperature': forms.NumberInput(attrs={
                'placeholder': 'temperature',
                'class': 'form-control',
                'step': '0.1',
            }),
            'weight': forms.NumberInput(attrs={
                'placeholder': 'weight',
                'class': 'form-control',
                'step': '0.1',
            }),
            'height': forms.NumberInput(attrs={
                'placeholder': 'height',
                'class': 'form-control',
                'step': '0.1',
            }),
        }

