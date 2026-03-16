from django import forms
from .models import Subtask, Employee

class SubtaskForm(forms.ModelForm):
    class Meta:
        model = Subtask
        fields = ['stage_number', 'title', 'description', 'output', 'priority',
                 'performers', 'responsible', 'planned_start', 'planned_end', 
                 'status', 'notes']
        widgets = {
            'stage_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'output': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'performers': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Выберите исполнителей...'
            }),
            'responsible': forms.Select(attrs={'class': 'form-control select2'}),
            'planned_start': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'planned_end': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.task = kwargs.pop('task', None)
        super().__init__(*args, **kwargs)
        
        # Ограничиваем выбор исполнителей активными сотрудниками
        self.fields['performers'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['responsible'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        
        # Автоматическое заполнение номера этапа при создании
        if self.task and not self.instance.pk:
            last_stage = self.task.subtasks.order_by('-stage_number').first()
            if last_stage:
                self.fields['stage_number'].initial = last_stage.stage_number + 1
            else:
                self.fields['stage_number'].initial = 1
    
    def clean(self):
        cleaned_data = super().clean()
        performers = cleaned_data.get('performers')
        responsible = cleaned_data.get('responsible')
        planned_start = cleaned_data.get('planned_start')
        planned_end = cleaned_data.get('planned_end')
        
        # Проверка: ответственный должен быть среди исполнителей
        if responsible and performers and responsible not in performers:
            raise forms.ValidationError("Ответственный должен быть выбран из списка исполнителей")
        
        # Проверка дат
        if planned_start and planned_end and planned_end < planned_start:
            raise forms.ValidationError("Дата окончания не может быть раньше даты начала")
        
        return cleaned_data


class SubtaskBulkCreateForm(forms.Form):
    """Форма для массового создания этапов"""
    stages_data = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 10,
            'class': 'form-control',
            'placeholder': 'Введите данные в формате: Номер;Название;Приоритет;Описание;Исполнители(через запятую)\nПриоритет: low, medium, high, critical\nПример:\n1;Анализ требований;high;Собрать требования;Иванов И.И.,Петров П.П.\n2;Проектирование;critical;Создать архитектуру;Сидоров С.С.'
        }),
        label='Данные этапов'
    )
    
    def clean_stages_data(self):
        data = self.cleaned_data['stages_data']
        lines = data.strip().split('\n')
        stages = []
        errors = []
        
        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            parts = [p.strip() for p in line.split(';')]
            if len(parts) < 2:
                errors.append(f"Строка {i}: недостаточно данных. Минимум: номер;название")
                continue
            
            try:
                stage_num = int(parts[0])
                stage = {
                    'stage_number': stage_num,
                    'title': parts[1],
                    'priority': parts[2] if len(parts) > 2 else 'medium',
                    'description': parts[3] if len(parts) > 3 else '',
                    'performers': parts[4] if len(parts) > 4 else ''
                }
                
                # Проверка валидности приоритета
                if stage['priority'] not in dict(Subtask.PRIORITY_CHOICES):
                    errors.append(f"Строка {i}: недопустимый приоритет '{stage['priority']}'. Допустимые: low, medium, high, critical")
                    continue
                    
                stages.append(stage)
            except ValueError:
                errors.append(f"Строка {i}: номер этапа должен быть числом")
        
        if errors:
            raise forms.ValidationError("\n".join(errors))
        
        return stages