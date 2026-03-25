from django.core.management.base import BaseCommand
from tasks.models import Subtask, ResearchProduct

class Command(BaseCommand):
    help = 'Migrate products from subtask.output to ResearchProduct model'

    def handle(self, *args, **options):
        for subtask in Subtask.objects.all():
            if subtask.output and 'Ожидаемая продукция:' in subtask.output:
                products_text = subtask.output.replace('Ожидаемая продукция:', '').strip()
                for line in products_text.split('\n'):
                    line = line.strip()
                    if line.startswith('•'):
                        product_name = line[1:].strip()
                        # Создаем продукцию, если её еще нет
                        product, created = ResearchProduct.objects.get_or_create(
                            subtask=subtask,
                            name=product_name,
                            defaults={'description': f'Продукция подэтапа {subtask.title}'}
                        )
                        if created:
                            self.stdout.write(f'Created product: {product_name}')
        
        self.stdout.write(self.style.SUCCESS('Migration completed'))