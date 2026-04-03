# tasks/forms_product.py (новый файл)

from django import forms
from django.core.exceptions import ValidationError
from .models import ResearchProduct, ProductPerformer, Employee


class ResearchProductForm(forms.ModelForm):
    """Форма для создания/редактирования научной продукции"""
    
    class Meta:
        model = ResearchProduct
        fields = [
            'name', 'product_type', 'description',
            'research_task', 'research_stage', 'research_substage',
            'planned_start', 'planned_end', 'due_date',
            'status', 'notes'
        ]
        widgets = {
            'planned_start': forms.DateInput(attrs={'type': 'date'}),
            'planned_end': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтрация выбора этапов по выбранной НИР
        if 'research_task' in self.data:
            try:
                task_id = int(self.data.get('research_task'))
                self.fields['research_stage'].queryset = ResearchStage.objects.filter(research_task_id=task_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['research_stage'].queryset = ResearchStage.objects.filter(
                research_task=self.instance.research_task
            )
    
    def clean(self):
        cleaned_data = super().clean()
        planned_start = cleaned_data.get('planned_start')
        planned_end = cleaned_data.get('planned_end')
        due_date = cleaned_data.get('due_date')
        
        if planned_start and planned_end and planned_start > planned_end:
            raise ValidationError('Дата начала не может быть позже даты окончания')
        
        if planned_end and due_date and planned_end > due_date:
            raise ValidationError('Срок выполнения (due_date) не может быть раньше планируемой даты окончания')
        
        return cleaned_data


class ProductPerformerForm(forms.ModelForm):
    """Форма для назначения исполнителя на продукцию"""
    
    class Meta:
        model = ProductPerformer
        fields = ['employee', 'role', 'contribution_percent', 'start_date', 'end_date', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        if self.product:
            # Исключаем уже назначенных сотрудников
            existing_employees = self.product.product_performers.values_list('employee_id', flat=True)
            self.fields['employee'].queryset = Employee.objects.filter(
                is_active=True
            ).exclude(
                id__in=existing_employees
            )
    
    def clean_contribution_percent(self):
        percent = self.cleaned_data.get('contribution_percent')
        if percent and (percent < 0 or percent > 100):
            raise ValidationError('Доля участия должна быть от 0 до 100%')
        return percent


class BulkAssignPerformersForm(forms.Form):
    """Форма для массового назначения исполнителей"""
    
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        label='Сотрудники'
    )
    role = forms.ChoiceField(
        choices=ProductPerformer.ROLE_CHOICES,
        label='Роль',
        initial='executor'
    )
    contribution_percent = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        label='Доля участия (%)'
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Дата начала работы'
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Дата окончания работы'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError('Дата начала не может быть позже даты окончания')
        
        return cleaned_data