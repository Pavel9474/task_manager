from django import forms
from .models import Task, Employee

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'start_time', 'end_time', 'due_date', 'priority', 'status', 'assigned_to']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'assigned_to': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'style': 'width: 100%',
                'data-placeholder': 'Выберите исполнителей...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['start_time', 'end_time', 'due_date', 'assigned_to']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Ограничиваем выбор только активными сотрудниками
        self.fields['assigned_to'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['assigned_to'].label = 'Исполнители'
        self.fields['assigned_to'].help_text = 'Выберите одного или нескольких исполнителей из команды'
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        due_date = cleaned_data.get('due_date')
        
        if start_time and end_time and end_time < start_time:
            raise forms.ValidationError("Время окончания не может быть раньше времени начала")
        
        if start_time and due_date and due_date < start_time:
            raise forms.ValidationError("Срок выполнения не может быть раньше времени начала")
        
        return cleaned_data