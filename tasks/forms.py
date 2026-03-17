from django import forms
from .models import Task, Employee, ResearchTask, ResearchStage, ResearchSubstage, ResearchProduct

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


class ResearchImportForm(forms.Form):
    docx_file = forms.FileField(
        label='Файл ТЗ (DOCX)',
        help_text='Загрузите файл технического задания в формате .docx',
        widget=forms.FileInput(attrs={'accept': '.docx', 'class': 'form-control'})
    )
    
    default_performers = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        label='Исполнители по умолчанию',
        help_text='Выберите исполнителей, которые будут назначены на все этапы',
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2'})
    )
    
    default_responsible = forms.ModelChoiceField(
        queryset=Employee.objects.filter(is_active=True),
        label='Ответственный по умолчанию',
        help_text='Выберите ответственного, который будет назначен на все этапы',
        required=False,
        widget=forms.Select(attrs={'class': 'select2'})
    )


class ResearchTaskForm(forms.ModelForm):
    class Meta:
        model = ResearchTask
        fields = ['title', 'tz_number', 'customer', 'executor', 'start_date', 'end_date', 'funding']
        widgets = {
            'title': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'tz_number': forms.TextInput(attrs={'class': 'form-control'}),
            'customer': forms.TextInput(attrs={'class': 'form-control'}),
            'executor': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'funding': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class ResearchStageForm(forms.ModelForm):
    class Meta:
        model = ResearchStage
        fields = ['stage_number', 'title', 'start_date', 'end_date', 'performers', 'responsible']
        widgets = {
            'stage_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'title': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'performers': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Выберите исполнителей...'
            }),
            'responsible': forms.Select(attrs={'class': 'form-control select2'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['performers'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['responsible'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')


class ResearchSubstageForm(forms.ModelForm):
    class Meta:
        model = ResearchSubstage
        fields = ['substage_number', 'title', 'description', 'start_date', 'end_date', 'performers', 'responsible']
        widgets = {
            'substage_number': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'performers': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Выберите исполнителей...'
            }),
            'responsible': forms.Select(attrs={'class': 'form-control select2'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.stage = kwargs.pop('stage', None)
        super().__init__(*args, **kwargs)
        self.fields['performers'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['responsible'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')


class ResearchProductForm(forms.ModelForm):
    class Meta:
        model = ResearchProduct
        fields = ['name', 'description', 'due_date', 'performers', 'responsible', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'performers': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Выберите исполнителей...'
            }),
            'responsible': forms.Select(attrs={'class': 'form-control select2'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.substage = kwargs.pop('substage', None)
        super().__init__(*args, **kwargs)
        self.fields['performers'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['responsible'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')

class TaskWithImportForm(forms.ModelForm):
    """Форма для создания задачи с возможностью импорта из ТЗ"""
    tz_file = forms.FileField(
        label='Импортировать из ТЗ (DOCX)',
        help_text='Загрузите файл технического задания для автоматического создания этапов и подэтапов',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.docx',
            'id': 'tzFileInput'
        })
    )
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'start_time', 'end_time', 'due_date', 
                 'priority', 'status', 'assigned_to']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'assigned_to': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Выберите исполнителей...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['start_time', 'end_time', 'due_date', 'assigned_to', 'tz_file']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        self.fields['assigned_to'].queryset = Employee.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['title'].required = False  # Делаем необязательным, т.к. может быть из файла
        self.fields['title'].help_text = 'Если не указано, будет взято из ТЗ'