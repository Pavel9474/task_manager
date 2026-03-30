import pandas as pd
import re
from datetime import datetime
from ..models import Employee, Department, Position, StaffPosition
from django.utils import timezone

class StaffImporter:
    """Импортер штатного расписания из Excel"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = pd.read_excel(file_path, header=None)
        print(f"Загружен файл: {file_path}")
        print(f"Размер таблицы: {self.df.shape}")
        
        # Словари для хранения созданных объектов
        self.departments = {}  # номер -> объект Department
        self.positions = {}     # название должности -> объект Position
        self.employees = {}     # ФИО -> объект Employee
    
    def parse_fio(self, fio_str):
        """Парсинг ФИО из строки"""
        if not fio_str or pd.isna(fio_str) or fio_str == 'Вакансия':
            return None, None, None
        
        # Убираем (Озёрск) и другие пометки в скобках
        clean_fio = re.sub(r'\s*\([^)]*\)', '', fio_str).strip()
        
        # Разбиваем на части
        parts = clean_fio.split()
        if len(parts) == 3:
            last_name, first_name, patronymic = parts
        elif len(parts) == 2:
            last_name, first_name = parts
            patronymic = ''
        else:
            last_name = clean_fio
            first_name = ''
            patronymic = ''
        
        return last_name, first_name, patronymic
    
    def get_department_parent(self, dept_number):
        """Определение родительского подразделения по номеру"""
        if '.' not in dept_number:
            return None
        
        # Родительский номер - это номер без последней точки и всего после неё
        # Например: 9.1.1 -> 9.1, 9.11.3.1 -> 9.11.3
        parent_number = '.'.join(dept_number.split('.')[:-1])
        
        # Ищем родителя в уже созданных подразделениях
        if parent_number in self.departments:
            return self.departments[parent_number]
        
        # Если родитель еще не создан, создаем его рекурсивно
        # Но это не должно случиться, если мы обрабатываем строки по порядку
        print(f"    ⚠️ Родитель {parent_number} для {dept_number} еще не создан")
        return None
    
    def get_department_type(self, name):
        """Определение типа подразделения по названию"""
        name_lower = name.lower()
        if 'лаборатор' in name_lower:
            return 'laboratory'
        elif 'групп' in name_lower:
            return 'group'
        elif 'отделени' in name_lower:
            return 'division'
        elif 'служб' in name_lower:
            return 'service'
        elif 'дирекц' in name_lower or 'руководств' in name_lower:
            return 'directorate'
        else:
            return 'department'
    
    def get_or_create_department(self, dept_number, name):
        """Создание или получение подразделения по номеру"""
        if dept_number in self.departments:
            return self.departments[dept_number]
        
        # Определяем родителя
        parent = self.get_department_parent(dept_number)
        
        # Определяем тип
        dept_type = self.get_department_type(name)
        
        # Создаем подразделение
        department = Department.objects.create(
            name=name,
            parent=parent,
            type=dept_type
        )
        
        # Сохраняем в словарь
        self.departments[dept_number] = department
        
        # Формируем отступы для красивого вывода
        level = dept_number.count('.') if dept_number else 0
        indent = "  " * level
        parent_info = f" (родитель: {parent.name})" if parent else ""
        print(f"{indent}✅ Создано подразделение: {dept_number} - {department.full_path}{parent_info}")
        
        return department
    
    def get_or_create_position(self, position_name, category=None):
        """Создание или получение должности"""
        if position_name in self.positions:
            return self.positions[position_name]
        
        position = Position.objects.create(
            name=position_name,
            category=category
        )
        self.positions[position_name] = position
        return position
    
    def get_or_create_employee(self, fio_str, position_name=None):
        """Создание или получение сотрудника по ФИО с указанием должности"""
        if fio_str in self.employees:
            return self.employees[fio_str]
        
        last_name, first_name, patronymic = self.parse_fio(fio_str)
        if not last_name:
            return None
        
        # Проверяем, есть ли уже такой сотрудник
        try:
            employee = Employee.objects.get(
                last_name=last_name,
                first_name=first_name,
                patronymic=patronymic or ''
            )
            # Если сотрудник существует, обновляем его должность
            if position_name:
                employee.position = position_name
                employee.save(update_fields=['position'])
            print(f"    🔄 Найден существующий сотрудник: {employee.full_name}")
        except Employee.DoesNotExist:
            # Создаем нового сотрудника
            employee = Employee.objects.create(
                last_name=last_name,
                first_name=first_name,
                patronymic=patronymic or '',
                position=position_name or 'Сотрудник',
                email=f"{last_name.lower()}.{first_name.lower()}@example.com".replace(' ', ''),
                is_active=True
            )
            print(f"    ✅ Создан новый сотрудник: {employee.full_name} - {position_name}")
        
        self.employees[fio_str] = employee
        return employee
    
    def parse_workload(self, value):
        """Парсинг ставки (1, 0.5, 0.25 и т.д.)"""
        if pd.isna(value) or value == '':
            return 1.0
        
        try:
            return float(value)
        except:
            return 1.0
    
    def parse_employment_type(self, value):
        """Парсинг типа занятости"""
        if pd.isna(value) or value == '':
            return 'main'
        
        value_lower = str(value).lower()
        
        if 'внутреннее совместительство' in value_lower:
            return 'internal_combination'
        elif 'внешнее совместительство' in value_lower:
            return 'external_combination'
        elif 'совмещение' in value_lower:
            return 'combination'
        elif 'декрет' in value_lower:
            return 'decree'
        elif 'надбавк' in value_lower:
            return 'allowance'
        elif 'вакансия' in value_lower:
            return 'vacant'
        else:
            return 'main'
    
    def import_staff(self):
            # ОТЛАДКА: Вывести все строки, где есть фамилии Аклеев, Котиков, Кривощапов
        print("\n🔍 ПОИСК КОНКРЕТНЫХ СОТРУДНИКОВ:")
        for idx, row in self.df.iterrows():
            if idx < 2:
                continue
            row_data = row.values
            # Проверяем все ячейки строки на наличие фамилий
            for cell in row_data:
                if pd.isna(cell):
                    continue
                cell_str = str(cell).lower()
                if any(name in cell_str for name in ['аклеев', 'котиков', 'кривощапов']):
                    print(f"\n  Строка {idx + 1}:")
                    for i, val in enumerate(row_data[:10]):  # Показываем первые 10 колонок
                        print(f"    Колонка {i}: {val}")
                    break
        """Основной метод импорта"""
        print("\n=== НАЧАЛО ИМПОРТА ШТАТНОГО РАСПИСАНИЯ ===\n")
        
        # Сначала собираем все подразделения
        print("📋 СБОР ПОДРАЗДЕЛЕНИЙ...\n")
        
        departments_data = []
        
        for idx, row in self.df.iterrows():
            if idx < 2:  # Пропускаем заголовки
                continue
            
            row_data = row.values
            
            # Получаем номер подразделения (первая колонка)
            dept_number = str(row_data[0]).strip() if not pd.isna(row_data[0]) else ''
            dept_name = str(row_data[1]).strip() if len(row_data) > 1 and not pd.isna(row_data[1]) else ''
            
            # Пропускаем итоговые строки
            if 'Итого' in dept_name:
                continue
            
            # Если это строка с подразделением (есть номер и название)
            if dept_number and dept_name and re.match(r'^[\d\.]+$', dept_number):
                departments_data.append((dept_number, dept_name))
                print(f"  Найдено подразделение: {dept_number} - {dept_name}")
        
        # Сортируем подразделения по номеру (чтобы родители создавались раньше детей)
        departments_data.sort(key=lambda x: x[0])
        
        print("\n🏗️ СОЗДАНИЕ СТРУКТУРЫ ПОДРАЗДЕЛЕНИЙ...\n")
        
        # Создаем подразделения
        for dept_number, dept_name in departments_data:
            self.get_or_create_department(dept_number, dept_name)
        
        print("\n👥 ИМПОРТ СОТРУДНИКОВ...\n")
        
        # Проходим по строкам таблицы для импорта сотрудников
        current_department = None
        imported_count = 0
        skipped_count = 0
        
        for idx, row in self.df.iterrows():
            if idx < 2:  # Пропускаем заголовки
                continue
            
            row_data = row.values
            
            # Получаем номер подразделения
            dept_number = str(row_data[0]).strip() if not pd.isna(row_data[0]) else ''
            
            # Если это строка с подразделением, запоминаем текущее подразделение
            if len(row_data) > 4 and not pd.isna(row_data[4]) and str(row_data[4]).strip() and str(row_data[4]).strip() != 'Вакансия':
                # Это строка с сотрудником - используем текущий department
                pass
            # Иначе если в колонке 0 есть номер подразделения - обновляем current_department
            elif dept_number and re.match(r'^[\d\.]+$', dept_number):
                if dept_number in self.departments:
                    current_department = self.departments[dept_number]
                continue
            
            # Если это строка с сотрудником
            if len(row_data) > 4:
                pkg = str(row_data[2]).strip() if not pd.isna(row_data[2]) else ''  # ПКГ
                position_name = str(row_data[3]).strip() if not pd.isna(row_data[3]) else ''  # Должность
                fio = str(row_data[4]).strip() if len(row_data) > 4 and not pd.isna(row_data[4]) else ''  # ФИО
                workload = row_data[5] if len(row_data) > 5 and not pd.isna(row_data[5]) else 1.0
                employment_type_str = row_data[6] if len(row_data) > 6 else ''
                
                if not position_name or position_name == 'ПКГ':
                    continue
                
                # Определяем уровень вложенности для отступа
                level = dept_number.count('.') if dept_number else 0
                indent = "  " * level if current_department else ""
                
                print(f"{indent}👤 Строка {idx + 1}: {position_name} - {fio}")
                
                try:
                    # Получаем или создаем должность в справочнике
                    position = self.get_or_create_position(position_name, pkg)
                    
                    # Если это вакансия
                    if 'вакансия' in fio.lower() or not fio:
                        employee = None
                        print(f"{indent}  📍 Вакансия: {position_name}")
                    else:
                        # Получаем или создаем сотрудника с указанием должности
                        employee = self.get_or_create_employee(fio, position_name)
                        if not employee:
                            print(f"{indent}  ⚠️ Не удалось распознать ФИО: {fio}")
                            continue
                    
                    # Парсим ставку и тип занятости
                    workload_value = self.parse_workload(workload)
                    employment_type = self.parse_employment_type(employment_type_str)
                    
                    # Создаем штатную единицу
                    if current_department:
                        staff_position = StaffPosition.objects.create(
                            employee=employee,
                            department=current_department,
                            position=position,
                            workload=workload_value,
                            employment_type=employment_type,
                            notes=f"ПКГ: {pkg}" if pkg else ''
                        )
                        print(f"{indent}  ✅ Добавлена штатная единица")
                        imported_count += 1
                    else:
                        print(f"{indent}  ⚠️ Нет текущего подразделения для позиции")
                        skipped_count += 1
                        
                except Exception as e:
                    print(f"{indent}  ❌ Ошибка: {e}")
                    skipped_count += 1
        
        print(f"\n=== ИТОГ ИМПОРТА ===")
        print(f"✅ Импортировано штатных единиц: {imported_count}")
        print(f"⚠️ Пропущено: {skipped_count}")
        print(f"📊 Создано подразделений: {Department.objects.count()}")
        print(f"📊 Создано должностей: {Position.objects.count()}")
        print(f"📊 Сотрудников в базе: {Employee.objects.count()}")
        
        return imported_count