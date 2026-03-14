from django import forms
from .models import Employee
import pandas as pd
from django.core.exceptions import ValidationError

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'last_name', 'first_name', 'patronymic', 'position',
            'email', 'phone', 'department', 'laboratory',
            'hire_date', 'is_active', 'notes'
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'placeholder': '+7 (999) 123-45-67'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['is_active', 'notes']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Добавляем звездочку для обязательных полей
        self.fields['last_name'].label = 'Фамилия *'
        self.fields['first_name'].label = 'Имя *'
        self.fields['position'].label = 'Должность *'
        self.fields['email'].label = 'Email *'
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Очищаем телефон от лишних символов
            cleaned = ''.join(filter(str.isdigit, phone))
            if len(cleaned) < 10:
                raise ValidationError('Телефон должен содержать минимум 10 цифр')
        return phone


class EmployeeImportForm(forms.Form):
    excel_file = forms.FileField(
        label='Excel файл',
        help_text='Загрузите файл в формате .xlsx или .xls',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )
    
    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']
        if not file.name.endswith(('.xlsx', '.xls')):
            raise ValidationError('Пожалуйста, загрузите файл Excel (.xlsx или .xls)')
        return file