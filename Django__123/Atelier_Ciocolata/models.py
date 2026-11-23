from django.db import models
from django.utils.translation import gettext_lazy
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
import uuid
from django.db.models.functions import Lower
  
#models are datele      

class Organizator(models.Model):     
    class Meta:        
        ordering = ['nume']
        verbose_name = "Organizator"
        verbose_name_plural = "Organizatori"
        get_latest_by = ['data_creare','inceput_colaborare','data_actualizare']
        indexes = [
            models.Index(fields=['nume'], name='nume_idx'),
            models.Index(fields=['email', 'activ'], name='email_activ_idx'),
            models.Index(fields=['-inceput_colaborare'], name='colaborare_idx'),
        ]

    nume = models.CharField(max_length=100)
    nume_abreviat = models.CharField(max_length=10, blank=True)
    persoana_juridica=models.BooleanField(default=True)
    vip=models.BooleanField(default=False)
    email = models.EmailField(unique=True, error_messages={
        'unique': 'Adresa de email este deja folosită.',
        'invalid': 'Introduceți o adresă de email validă.',
    })
    sigla = models.ImageField(upload_to='organizatori/', null=True)
    inceput_colaborare = models.DateTimeField(null=True)
    data_creare = models.DateTimeField(default=timezone.now, null=True)    
    data_actualizare = models.DateTimeField(auto_now=True)
    activ=models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nume} ({self.nume_abreviat})"

class Locatie(models.Model):
    class Meta:
        abstract = True
        

    adresa = models.CharField(max_length=255)
    oras = models.CharField(max_length=100)
    judet = models.CharField(max_length=110)    
    cod_postal = models.CharField(max_length=10,null=True, default="012345")  



class SediuEveniment(Locatie):
    class Meta:        
        verbose_name = "Sediu de eveniment"
        verbose_name_plural = "Sedii de evenimente"
        ordering = ['nume']
    nume = models.CharField(max_length=255, unique=True)    
    def __str__(self):
        return f"{self.nume}, {self.oras}"
    
# class MagazinFizic(Locatie):
#     class Meta:        
#         verbose_name = "Magazin Fizic"
#         verbose_name_plural = "Magazine Fizice"
        
#     nume = models.CharField(max_length=100, unique=True)
#     class CStatus(models.TextChoices):
#         ACTIV= "activ", "In funcționare"
#         RENOVARE= "renovare", "In renovare"
#         INCHIS= "inchis", "Cofetaria e temporar închisă"
#     status=models.CharField(
#         choices=CStatus.choices,
#         default=CStatus.ACTIV
#     )    
    
#     def __str__(self):
#         return f"{self.nume}, {self.oras} ({self.adresa})"
    

# class OrarSediu(models.Model):
#     ZILE = [
#         (1, 'Luni'),
#         (2, 'Marți'),
#         (3, 'Miercuri'),
#         (4, 'Joi'),
#         (5, 'Vineri'),
#         (6, 'Sâmbătă'),
#         (7, 'Duminică'),
#     ]
#     magazin = models.ForeignKey(MagazinFizic, on_delete=models.CASCADE, related_name='orare')
#     zi = models.IntegerField(choices=ZILE)
#     ora_deschidere = models.TimeField(null=True)
#     ora_inchidere = models.TimeField(null=True)
#     este_inchis = models.BooleanField(default=False)
    
#     class Meta:
#         unique_together = ('magazin', 'zi')
#         ordering = ['zi']

#     def __str__(self):
#         status = "Închis" if self.este_inchis else f"{self.ora_deschidere} - {self.ora_inchidere}"
#         return f"{self.get_zi_display()}: {status}"    
    
class Ambalaj(models.Model):
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(nivel_rezistenta__lte=10) & models.Q(nivel_rezistenta__gte=1),
                name='limite_rezista_ambalaj',
                violation_error_message="Nivelul de rezistență trebuie să fie între 1 și 10 inclusiv!"
            ) 
        ]       
        verbose_name = "Ambalaj"
        verbose_name_plural = "Ambalaje"
        
    nume=models.CharField(max_length=200, unique=True, error_messages={
        'unique': 'Există deja un ambalaj cu acest nume.',
        'max_length': 'Numele ambalajului este prea lung.',
    })
    culoare=models.CharField(max_length=100, null=True)
    nivel_rezistenta=models.PositiveIntegerField(
        help_text="Valori între 1 și 10. Un număr mai mare indică rezistență mai mare",
        error_messages={'invalid': 'Introduceți un număr între 1 și 10.'},
        null=True
    )
    descriere = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nume}: {self.culoare}" 



class Categorie(models.Model):
    class Meta:
        verbose_name = "Categorie"
        verbose_name_plural = "Categorii"
        ordering = ['nume']

    nume = models.CharField(max_length=100, unique=True, error_messages={
        'unique': 'Există deja o categorie cu acest nume.',
        'max_length': 'Numele categoriei este prea lung.',
    })
    descriere = models.TextField()
    culoare = models.CharField(max_length=30, help_text="Culoarea reprezentativă a categoriei.")
    sigla = models.CharField(max_length=255, help_text="Calea imaginii sau numele pictogramei.")
    ordine = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nume


class Prajitura(models.Model):
    class Meta:
        verbose_name = "Prăjitură"
        verbose_name_plural = "Prăjituri"
        ordering = ['nume']
        indexes = [
            models.Index(Lower('nume'), name='parjituri_nume_litere_mici_idx'),
            models.Index(
                fields=['stoc'],
                name='prajituri_disponibile_idx',
                condition=models.Q(stoc__gt=0)
            )
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(pret__gte=0), name='prajitura_pret_pozitiv'),
            models.CheckConstraint(condition=models.Q(gramaj__gt=0), name='prajitura_gramaj_pozitiv'),
            models.CheckConstraint(
                condition=models.Q(stoc_rezervat__lte=models.F('stoc')),
                name='prajitura_stoc_rezervat_valid',
            ),
        ]
    class TipProdus(models.TextChoices):
        COMANDA_SPECIALA = 'comanda speciala', gettext_lazy('comanda speciala')
        ANIVERSARA = 'aniversara', gettext_lazy('aniversara')
        EDITIE_LIMITATA = 'editie limitata', gettext_lazy('editie limitata')
        PENTRU_COPII = 'pentru copii', gettext_lazy('pentru copii')
        DIETETETIC = 'dietetic', gettext_lazy('dietetic')
        COMUNA = 'comuna', gettext_lazy('comuna')          
    nume = models.CharField(
        max_length=50, 
        unique=True,
        error_messages={
            'unique': "O prăjitură cu acest nume există deja în meniu.",
            'blank': "Te rugăm să introduci un nume, nu poate fi gol.",
            'max_length': "Numele este prea lung (maxim 50 caractere)."
        }
    )
    descriere = models.TextField(null=True)
    pret = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=10,
        error_messages={
            "max_digits": "Numărul total de cifre nu poate depăși 8.",
            "max_decimal_places": "Nu pot fi mai mult de 2 zecimale.",
            "invalid": "Introduceți un număr valid (de exemplu: 12.55)."
        }
    )
    # proprietatati ale prăjiturilor
    gramaj = models.PositiveIntegerField(default=10, help_text="Gramajul unei porții, în grame.")
    calorii = models.PositiveIntegerField(default=10, help_text="Numărul de calorii pentru o porție.")
    stoc = models.PositiveIntegerField(default=0)
    stoc_rezervat = models.PositiveIntegerField(default=0, help_text="Prajiturile rezervate - sunt separate de stocul efectiv")
    tip_produs = models.CharField(max_length=50,
        choices=TipProdus.choices,
        default=TipProdus.COMUNA)
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name='prajituri')
    pt_diabetici=models.BooleanField(default=False)
    imagine=models.ImageField(upload_to='prajituri/', null=True, blank=True)
    ingrediente = ArrayField(
        models.CharField(max_length=50, blank=True), 
        default=list, blank=True, null=True,
        help_text="Lista ingredientelor folosite la preparare."
    )
    ambalaje=models.ManyToManyField(Ambalaj, related_name="ambalaje",blank=True)    
    data_creare = models.DateTimeField(auto_now_add=True, null=True)
    
    def __str__(self):
        return f"{self.nume}"    
    
    # def save(self, *args, **kwargs):
    #     from .signals import pret_prajitura_modificat
    #     if self.pk:
    #         prajitura_veche = Prajitura.objects.get(pk=self.pk)
    #         pret_vechi = prajitura_veche.pret
    #         pret_nou = self.pret

    #         if pret_vechi != pret_nou:
    #             pret_prajitura_modificat.send(
    #                 sender=self.__class__, 
    #                 instance=self, 
    #                 pret_vechi=pret_vechi, 
    #                 pret_nou=pret_nou
    #             )


    #     super().save(*args, **kwargs)
        
    



class Eveniment(models.Model):
    class Meta:
        verbose_name = "Eveniment"
        verbose_name_plural = "Evenimente"
        constraints = [
            models.CheckConstraint(condition=models.Q(capacitate__gt=0), name='eveniment_capacitate_pozitiva')
        ]

    id_eveniment = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    titlu = models.CharField(max_length=200)
    descriere = models.TextField()
    TIPURI_EVENIMENT = [
        ('conferinta', 'Conferinta'), ('workshop', 'Workshop'),
        ('intalnire', 'Intalnire'), ('webinar', 'Webinar')]
    tip_eveniment = models.CharField(max_length=50, choices=TIPURI_EVENIMENT)
    capacitate = models.PositiveIntegerField()
    este_public = models.BooleanField(default=True)
    imagine = models.ImageField(upload_to='evenimente/', null=True, blank=True)
    website = models.URLField(blank=True, null=True)
    slug = models.SlugField(unique=True, error_messages={
        'unique': 'Acest identificator este deja folosit.',
        'invalid': 'Folosiți doar litere, cifre, cratime sau underscore.',
    })
    data_creare = models.DateTimeField(auto_now_add=True)
    data_actualizare = models.DateTimeField(auto_now=True)
    sediu = models.ForeignKey(SediuEveniment, on_delete=models.SET_NULL, null=True, related_name="evenimente")
    organizator = models.ForeignKey(Organizator, on_delete=models.SET_NULL, null=True, related_name="evenimente")
    prajituri=models.ManyToManyField(
        Prajitura,
        related_name="evenimente",
        through='PrajituriEvenimente'
    )
    
    def __str__(self):
        return f"{self.titlu}" 
    
class PrajituriEvenimente(models.Model):
    class Meta:
        verbose_name = "Prăjitură la eveniment"
        verbose_name_plural = "Prăjituri la evenimente"
        constraints = [
            models.UniqueConstraint(
                fields=['prajitura', 'eveniment'],
                name='unicitate_prajitura_eveniment'
            ),
            models.CheckConstraint(
                condition=models.Q(nr_prajituri__gt=0) | models.Q(nr_prajituri__isnull=True),
                name='eveniment_nr_prajituri_pozitiv'
            ),
        ]
    prajitura=models.ForeignKey(Prajitura,on_delete=models.CASCADE)
    eveniment=models.ForeignKey(Eveniment,on_delete=models.CASCADE)
    nr_prajituri=models.PositiveIntegerField(null=True)
    def __str__(self):
        return f"{self.prajitura.nume} - {self.eveniment.titlu}" 
    
class IstoricPret(models.Model):
    class Meta:
        verbose_name = "Istoric de preț"
        verbose_name_plural = "Istorice de preț"
        constraints = [
            models.CheckConstraint(condition=models.Q(pret__gte=0), name='istoric_pret_pozitiv')
        ]
    
    pret=models.DecimalField(max_digits=8, decimal_places=2)
    data_pret_nou = models.DateTimeField(auto_now_add=True)    
    produs=models.ForeignKey(Prajitura, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.produs.nume} - {self.pret}" 


    
# import zoneinfo
# class CustomUser(AbstractUser):
#     class Meta:
#         verbose_name = "Utilizator"
#         verbose_name_plural = "Utilizatori"
#     telefon = models.CharField(max_length=15, blank=True)    
#     email_serviciu=models.EmailField(null=True,blank=True)
#     FUS_ORAR_CHOICES = [(tz, tz) for tz in zoneinfo.available_timezones()]
#     fus_orar = models.CharField(max_length=64, choices=FUS_ORAR_CHOICES, default='UTC', null=True)
    

# class Post(models.Model):
#     nume = models.CharField(max_length=50, unique=True)
#     descriere=models.TextField(null=True)
#     baza_salariu=models.DecimalField(max_digits=8, decimal_places=2)
#     zile_concediu=models.PositiveIntegerField(default=20)

# class InfoAngajat(models.Model):
#     spor_salariu=models.DecimalField(max_digits=8, decimal_places=2)
#     data_angajarii=models.DateTimeField()   
#     post=models.ForeignKey(Post, on_delete=models.CASCADE)
#     magazin=models.ForeignKey(MagazinFizic, on_delete=models.CASCADE)
#     dateAngajat=models.OneToOneField(
#         CustomUser, #clasa personalizată pentru utilizatori
#         on_delete=models.CASCADE, 
#         help_text="Legatura cu user-ul inregistrat pe site, pentru angajat"
#     )   

# class RevistaPromotionala(models.Model):
#     titlu= models.CharField(max_length=200, default="Revista promo")
#     data_aparitie=models.DateField()
#     editor=models.ForeignKey(InfoAngajat, on_delete=models.CASCADE, null=True)
    
# class ArticolRevistaPromo(models.Model):
#     titlu= models.CharField(max_length=200)
#     autor=models.ForeignKey(InfoAngajat, on_delete=models.RESTRICT)
#     revista=models.ForeignKey(RevistaPromotionala, on_delete=models.CASCADE)









