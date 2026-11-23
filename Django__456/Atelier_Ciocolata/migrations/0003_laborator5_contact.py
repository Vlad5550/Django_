from django.db import migrations, models
import django.db.models.deletion


def adauga_date_initiale(apps, schema_editor):
    Departament = apps.get_model('Atelier_Ciocolata', 'Departament')
    TipMesaj = apps.get_model('Atelier_Ciocolata', 'TipMesaj')
    Legatura = apps.get_model('Atelier_Ciocolata', 'TipMesajDepartament')
    baza = schema_editor.connection.alias

    departamente = {}
    for nume, slug in [
        ('Suport', 'suport'), ('Administrație', 'administratie'),
        ('Comenzi', 'comenzi'), ('QA', 'qa'), ('Angajări', 'angajari'),
    ]:
        departamente[nume] = Departament.objects.using(baza).create(nume=nume, slug=slug)

    reguli = [
        ('reclamație', 2, ['Suport', 'Administrație']),
        ('întrebare', 2, ['Suport', 'Comenzi']),
        ('review', 4, ['QA', 'Administrație']),
        ('cerere', 4, ['Angajări', 'Administrație', 'Comenzi']),
        ('programare', 2, ['Comenzi', 'Administrație']),
    ]
    for nume, minim, lista in reguli:
        tip = TipMesaj.objects.using(baza).create(nume=nume, minim_zile=minim)
        for departament in lista:
            Legatura.objects.using(baza).create(tip_mesaj=tip, departament=departamente[departament])


def sterge_date_initiale(apps, schema_editor):
    Departament = apps.get_model('Atelier_Ciocolata', 'Departament')
    TipMesaj = apps.get_model('Atelier_Ciocolata', 'TipMesaj')
    TipMesaj.objects.all().delete()
    Departament.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [('Atelier_Ciocolata', '0002_prajitura_taguri')]

    operations = [
        migrations.CreateModel(
            name='Departament',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nume', models.CharField(max_length=80, unique=True)),
                ('slug', models.SlugField(max_length=90, unique=True)),
            ],
            options={'verbose_name': 'Departament', 'verbose_name_plural': 'Departamente', 'ordering': ['nume']},
        ),
        migrations.CreateModel(
            name='TipMesaj',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nume', models.CharField(max_length=40, unique=True)),
                ('minim_zile', models.PositiveSmallIntegerField(default=2)),
            ],
            options={'verbose_name': 'Tip mesaj', 'verbose_name_plural': 'Tipuri mesaje', 'ordering': ['nume']},
        ),
        migrations.CreateModel(
            name='TipMesajDepartament',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('departament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Atelier_Ciocolata.departament')),
                ('tip_mesaj', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Atelier_Ciocolata.tipmesaj')),
            ],
            options={'verbose_name': 'Tip mesaj - departament', 'verbose_name_plural': 'Tip mesaj - departamente'},
        ),
        migrations.AddField(
            model_name='tipmesaj', name='departamente',
            field=models.ManyToManyField(related_name='tipuri_mesaj', through='Atelier_Ciocolata.TipMesajDepartament', to='Atelier_Ciocolata.departament'),
        ),
        migrations.AddConstraint(
            model_name='tipmesajdepartament',
            constraint=models.UniqueConstraint(fields=('tip_mesaj', 'departament'), name='unic_tip_departament'),
        ),
        migrations.RunPython(adauga_date_initiale, sterge_date_initiale),
    ]
