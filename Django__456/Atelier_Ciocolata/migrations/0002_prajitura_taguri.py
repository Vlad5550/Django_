from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('Atelier_Ciocolata', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='prajitura',
            name='taguri',
            field=ArrayField(base_field=models.CharField(blank=True, max_length=50), blank=True, default=list, size=None, help_text='Cuvinte cheie pentru filtrarea produselor.'),
        ),
    ]
