from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

#  Defineste scturctura bazei de date

#  Categorii
class Categorie(models.Model):
    nume = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True)
    descriere = models.TextField(null=True, blank=True)
    culoare = models.CharField(max_length=7, default="#6B2E1F")
    sigla = models.CharField(max_length=50, default="fa-cookie-bite")
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordine", "nume"]

    def __str__(self):
        return self.nume


#  Branduri
class Brand(models.Model):
    nume = models.CharField(max_length=80, unique=True)
    tara_origine = models.CharField(max_length=50, null=True, blank=True)
    site_web = models.URLField(null=True, blank=True)

    class Meta:
        ordering = ["nume"]

    def __str__(self):
        return self.nume


#  Ambalaje
class Ambalaj(models.Model):
    class Material(models.TextChoices):
        CARTON = "carton", "Carton"
        STICLA = "sticla", "Sticlă"
        METAL = "metal", "Metal"
        PLASTIC = "plastic", "Plastic"
        TEXTIL = "textil", "Textil"

    material = models.CharField(max_length=20, choices=Material.choices, default=Material.CARTON)
    nume = models.CharField(max_length=60, unique=True)
    capacitate_buc = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    reciclabil = models.BooleanField(default=True)

    def __str__(self):
        return self.nume


#  Ingrediente
class Ingredient(models.Model):
    nume = models.CharField(max_length=80, unique=True)
    origine = models.CharField(max_length=80, null=True, blank=True)
    certificat_bio = models.BooleanField(default=False)

    class Meta:
        ordering = ["nume"]

    def __str__(self):
        return self.nume


#  Sedii
class SediuCompanie(models.Model):
    nume = models.CharField(max_length=80, unique=True)
    adresa = models.CharField(max_length=180)
    telefon = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    sediu_principal = models.BooleanField(default=False)

    def __str__(self):
        return self.nume


#  Produse
class Produs(models.Model):
    class Tip(models.TextChoices):
        TABLETA = "tableta", "Tabletă"
        PRALINE = "praline", "Praline"
        TRUFE = "trufe", "Trufe"
        CREMA = "crema", "Cremă"
        CADOU = "cadou", "Pachet cadou"

    nume = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)
    descriere = models.TextField(null=True, blank=True)
    pret = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    gramaj_g = models.PositiveIntegerField(default=100, validators=[MinValueValidator(1)])
    procent_cacao = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    tip = models.CharField(max_length=20, choices=Tip.choices, default=Tip.TABLETA)
    disponibil = models.BooleanField(default=True)
    arome = models.JSONField(default=list, blank=True)
    imagine = models.ImageField(upload_to="produse/", null=True, blank=True)
    data_adaugare = models.DateTimeField(default=timezone.now, editable=False)

    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name="produse")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="produse")
    ambalaj = models.ForeignKey(Ambalaj, on_delete=models.PROTECT, related_name="produse")
    ingrediente = models.ManyToManyField(Ingredient, related_name="produse", blank=True)

    class Meta:
        ordering = ["nume"]

    def __str__(self):
        return self.nume


#  Loturi de producție
class LotProductie(models.Model):
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE, related_name="loturi")
    nr_lot = models.PositiveIntegerField()
    sediu = models.ForeignKey(SediuCompanie, on_delete=models.PROTECT, related_name="loturi")
    data_productie = models.DateField(default=timezone.localdate)
    data_expirare = models.DateField()
    cantitate = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["-data_productie"]
        constraints = [
            models.UniqueConstraint(fields=["produs", "nr_lot"], name="lot_produs_nr_unic")
        ]

    def __str__(self):
        return f"Lot {self.nr_lot} - {self.produs.nume}"
