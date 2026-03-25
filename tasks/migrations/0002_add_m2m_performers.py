from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='researchproduct',
            name='performers',
            field=models.ManyToManyField(blank=True, related_name='research_products', to='tasks.employee', verbose_name='Исполнители'),
        ),
    ]