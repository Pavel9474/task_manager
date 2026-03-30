from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from ..forms import StaffImportForm, ResearchImportForm
from ..utils.staff_importer import StaffImporter
from ..utils.docx_importer import ResearchDocxImporter
import tempfile
import os
from django.core.cache import cache



@login_required
def import_research_from_docx(request):
    """Импорт НИР из DOCX файла"""
    if request.method == 'POST':
        form = ResearchImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                docx_file = request.FILES['docx_file']
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                    for chunk in docx_file.chunks():
                        tmp_file.write(chunk)
                    tmp_path = tmp_file.name
                
                importer = ResearchDocxImporter(tmp_path)
                default_performers = form.cleaned_data['default_performers']
                
                # Импортируем с новыми полями
                task = importer.import_research(default_performers)
                
                os.unlink(tmp_path)
                
                messages.success(request, f'Успешно импортирована НИР: {task.title}')
                return redirect('research_task_detail', task_id=task.id)
                
            except Exception as e:
                messages.error(request, f'Ошибка при импорте: {str(e)}')
                import traceback
                traceback.print_exc()
    else:
        form = ResearchImportForm()
    
    return render(request, 'tasks/import_research.html', {'form': form})

@login_required
def preview_import(request):
    """Предпросмотр данных из ТЗ перед импортом"""
    if request.method == 'POST' and request.FILES.get('tz_file'):
        tz_file = request.FILES['tz_file']
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                for chunk in tz_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            importer = ResearchDocxImporter(tmp_path)
            tz_data = importer.parse_research_task()
            
            os.unlink(tmp_path)
            
            return JsonResponse({
                'success': True,
                'title': tz_data.get('title'),
                'stages_count': len(tz_data.get('stages', [])),
                'stages': tz_data.get('stages', [])
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def import_staff_from_excel(request):
    """Импорт штатного расписания из Excel"""
    if request.method == 'POST':
        form = StaffImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                excel_file = request.FILES['excel_file']
                
                # Сохраняем файл временно
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    for chunk in excel_file.chunks():
                        tmp_file.write(chunk)
                    tmp_path = tmp_file.name
                
                # Импортируем
                importer = StaffImporter(tmp_path)
                imported_count = importer.import_staff()
                
                # Удаляем временный файл
                import os
                os.unlink(tmp_path)
                
                # Очищаем кэш оргструктуры после импорта
                cache.delete('org_chart_data_v3')
                print(f"🗑️ Кэш оргструктуры очищен после импорта штатного расписания")
                
                messages.success(request, f'Успешно импортировано {imported_count} штатных единиц')
                return redirect('employee_list')
                
            except Exception as e:
                messages.error(request, f'Ошибка при импорте: {str(e)}')
    else:
        form = StaffImportForm()
    
    return render(request, 'tasks/import_staff.html', {'form': form})