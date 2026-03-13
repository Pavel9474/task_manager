from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'start_time', 'end_time', 'due_date', 'priority', 'status']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['start_time', 'end_time', 'due_date']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        due_date = cleaned_data.get('due_date')
        
        # Валидация: время окончания не может быть раньше времени начала
        if start_time and end_time and end_time < start_time:
            raise forms.ValidationError("Время окончания не может быть раньше времени начала")
        
        # Валидация: срок выполнения не может быть раньше времени начала
        if start_time and due_date and due_date < start_time:
            raise forms.ValidationError("Срок выполнения не может быть раньше времени начала")
        
        return cleaned_data