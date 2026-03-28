from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Удаляет все НИР и связанные данные'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Удалить без подтверждения',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Считаем количество
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tasks_researchtask")
            count = cursor.fetchone()[0]
        
        if count == 0:
            self.stdout.write(self.style.WARNING('Нет НИР для удаления'))
            return
        
        self.stdout.write(f'Будет удалено: {count} НИР')
        
        if not force:
            confirm = input('Удалить все НИР? (y/n): ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('Отменено'))
                return
        
        self.stdout.write('\n🗑️ Удаление...')
        
        with connection.cursor() as cursor:
            try:
                # Удаляем ProductPerformer
                cursor.execute("DELETE FROM tasks_productperformer WHERE product_id IN (SELECT id FROM tasks_researchproduct)")
                self.stdout.write('   Удалены назначения исполнителей')
                
                # Удаляем ResearchProduct
                cursor.execute("DELETE FROM tasks_researchproduct")
                self.stdout.write('   Удалена продукция')
                
                # Удаляем ResearchSubstage
                cursor.execute("DELETE FROM tasks_researchsubstage")
                self.stdout.write('   Удалены подэтапы')
                
                # Удаляем ResearchStage
                cursor.execute("DELETE FROM tasks_researchstage")
                self.stdout.write('   Удалены этапы')
                
                # Удаляем ResearchTaskFunding
                cursor.execute("DELETE FROM tasks_researchtaskfunding")
                self.stdout.write('   Удалено финансирование')
                
                # Удаляем ResearchTask
                cursor.execute("DELETE FROM tasks_researchtask")
                self.stdout.write('   Удалены НИР')
                
                self.stdout.write(self.style.SUCCESS('\n✅ Все НИР удалены'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\n❌ Ошибка: {e}'))