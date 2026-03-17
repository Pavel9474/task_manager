import re
from docx import Document
from datetime import datetime
from ..models import Subtask, Employee

class ResearchDocxImporter:
    def __init__(self, file_path):
        self.file_path = file_path
        self.doc = Document(file_path)
        print(f"Загружен документ: {file_path}")
        print(f"Количество параграфов: {len(self.doc.paragraphs)}")
        print(f"Количество таблиц: {len(self.doc.tables)}")
    
    def parse_research_task(self):
        """Парсинг ТЗ и возврат структуры данных"""
        result = {
            'title': self._extract_title(),
            'stages': self._extract_stages()
        }
        
        print(f"Найдено название: {result['title']}")
        print(f"Найдено этапов: {len(result['stages'])}")
        
        return result
    
    def _extract_title(self):
        """Извлечение названия ТЗ"""
        for paragraph in self.doc.paragraphs:
            if 'по теме:' in paragraph.text:
                match = re.search(r'по теме:\s*«(.+?)»', paragraph.text)
                if match:
                    return match.group(1)
                # Альтернативный формат
                match = re.search(r'по теме:\s*"(.+?)"', paragraph.text)
                if match:
                    return match.group(1)
        return None
    
    def _extract_stages(self):
        """Извлечение этапов из таблицы"""
        stages = []
        
        # Ищем таблицу с этапами
        target_table = None
        for table_idx, table in enumerate(self.doc.tables):
            if len(table.rows) > 15 and len(table.columns) == 4:
                target_table = table
                print(f"\n✅ Найдена таблица с этапами (индекс {table_idx + 1})")
                break
        
        if not target_table:
            print("❌ Таблица с этапами не найдена")
            return stages
        
        print(f"Анализ таблицы этапов:")
        print(f"  Всего строк: {len(target_table.rows)}")
        
        current_stage = None
        
        for row_idx, row in enumerate(target_table.rows):
            if row_idx < 2:  # Пропускаем первые две строки (заголовки)
                continue
                
            cells = [cell.text.strip() for cell in row.cells]
            if len(cells) < 4:
                continue
                
            stage_num = cells[0].strip()
            stage_title = cells[1].strip()
            stage_products = cells[2].strip() if len(cells) > 2 else ''
            
            # Пропускаем пустые строки
            if not stage_num and not stage_title:
                continue
            
            print(f"\n  Строка {row_idx + 1}: номер='{stage_num}', название='{stage_title[:50]}...'")
            
            # Проверяем, является ли строка этапом (целое число)
            if stage_num.isdigit():
                stage_number = int(stage_num)
                
                # Пропускаем строки с номерами колонок
                if stage_title == '2' or stage_title == '3' or stage_title == '4':
                    print(f"    Пропускаем строку-заголовок: {stage_title}")
                    continue
                
                current_stage = {
                    'number': stage_number,
                    'title': stage_title,
                    'products': self._parse_products(stage_products),
                    'substages': []
                }
                stages.append(current_stage)
                print(f"    ✅ Этап {stage_number}: {stage_title[:50]}...")
                
            # Проверяем, является ли строка подэтапом (число с точкой)
            elif '.' in stage_num and stage_num.replace('.', '').isdigit():
                if current_stage:
                    # Проверяем, что номер подэтапа соответствует текущему этапу
                    stage_main_num = int(stage_num.split('.')[0])
                    if stage_main_num == current_stage['number']:
                        substage = {
                            'number': stage_num,
                            'title': stage_title,
                            'products': self._parse_products(stage_products)
                        }
                        current_stage['substages'].append(substage)
                        print(f"    🔹 Подэтап {stage_num} добавлен к этапу {current_stage['number']}")
                    else:
                        print(f"    ⚠️ Подэтап {stage_num} не соответствует текущему этапу {current_stage['number']}, ищем подходящий этап")
                        # Ищем подходящий этап
                        found = False
                        for stage in stages:
                            if stage['number'] == stage_main_num:
                                substage = {
                                    'number': stage_num,
                                    'title': stage_title,
                                    'products': self._parse_products(stage_products)
                                }
                                stage['substages'].append(substage)
                                print(f"    🔹 Подэтап {stage_num} добавлен к этапу {stage['number']}")
                                found = True
                                break
                        if not found:
                            print(f"    ❌ Не найден этап {stage_main_num} для подэтапа {stage_num}")
                else:
                    print(f"    ⚠️ Нет текущего этапа для подэтапа {stage_num}")
        
        # Выводим итоговую структуру
        print("\n=== ИТОГОВАЯ СТРУКТУРА ===")
        for stage in stages:
            print(f"Этап {stage['number']}: {stage['title'][:50]}...")
            print(f"  Подэтапов: {len(stage['substages'])}")
            for substage in stage['substages']:
                print(f"    - {substage['number']}: {substage['title'][:50]}...")
                print(f"      Продукции: {len(substage.get('products', []))}")
        
        return stages
    
    def _parse_products(self, products_str):
        """Парсинг научно-технической продукции"""
        products = []
        if products_str and products_str != '-' and products_str.strip():
            # Разделяем по точке с запятой, точке или новой строке
            parts = re.split(r'[.;\n]\s*', products_str)
            for part in parts:
                part = part.strip()
                # Фильтруем пустые и слишком короткие строки
                if part and len(part) > 5 and not part.startswith(('http', 'www')):
                    # Убираем нумерацию в начале
                    part = re.sub(r'^\d+\.\s*', '', part)
                    products.append(part)
        return products
    
    def create_task_structure(self, task, stages_data):
        """Создание структуры этапов и подэтапов для задачи"""
        from ..models import Subtask
        
        print(f"\nСоздание структуры для задачи: {task.title}")
        print(f"Получено этапов: {len(stages_data)}")
        
        # ПРИНУДИТЕЛЬНО удаляем все существующие подэтапы для этой задачи
        print(f"Удаляем все существующие подэтапы для задачи {task.id}")
        deleted = Subtask.objects.filter(task=task).delete()
        print(f"Удалено: {deleted}")
        
        created_count = 0
        
        # Сначала создаем все основные этапы (целые числа)
        for stage_idx, stage_data in enumerate(stages_data):
            stage_number = stage_data['number']
            stage = Subtask.objects.create(
                task=task,
                stage_number=stage_number,
                title=stage_data['title'][:200],
                description=f"Этап {stage_data['number']} из ТЗ",
                status='pending',
                priority='medium'
            )
            print(f"  ✅ Создан этап {stage_number} ID: {stage.id}")
            created_count += 1
            
            # Сразу создаем подэтапы для этого этапа
            substages = stage_data.get('substages', [])
            for substage_data in substages:
                try:
                    stage_num = float(substage_data['number'])
                    
                    substage = Subtask.objects.create(
                        task=task,
                        stage_number=stage_num,
                        title=substage_data['title'][:200],
                        description=f"Подэтап {substage_data['number']} из ТЗ",
                        status='pending',
                        priority='medium'
                    )
                    print(f"    🔹 Создан подэтап {substage_data['number']} ID: {substage.id}")
                    created_count += 1
                    
                    # Сохраняем продукцию
                    if substage_data.get('products'):
                        products_text = "\n".join([f"• {p}" for p in substage_data['products']])
                        substage.output = f"Ожидаемая продукция:\n{products_text}"
                        substage.save()
                        
                except Exception as e:
                    print(f"    ❌ Ошибка создания подэтапа {substage_data.get('number')}: {e}")
        
        # Проверяем результат
        final_count = Subtask.objects.filter(task=task).count()
        print(f"\n✅ Всего создано подэтапов: {final_count}")
        
        # Выводим список для проверки
        print("\nСписок всех созданных подэтапов:")
        for s in task.subtasks.all().order_by('stage_number'):
            print(f"  {s.stage_number}: {s.title[:50]}...")