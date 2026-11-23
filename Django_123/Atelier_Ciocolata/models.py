from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
 
# LAB 3, TASK 1: modelele de mai jos corespund celor 7 entități din diagrama ER.
# Cerințele globale sunt marcate lângă câmpuri și constrângeri:
# 1) null=True: descrieri, țară, site, origine, email, procent cacao, imagine.
# 2) unique=True: nume/slug-uri unice, în afară de cheia primară.
# 3) EmailField, URLField și SlugField: email, site_web și slug.
# 4) Meta.ordering: ordonare implicită pentru cel puțin două modele.
# 5) choices: material ambalaj și tip produs.
# 6) default: valori inițiale, iar blank=True permite formular gol în Admin.
# 7) help_text: explicații vizibile sub câmpuri în formularele Admin.
# 8) DateTimeField: data_adaugare folosește timezone.now.
# 9) error_messages / validators: mesaje personalizate la validare.
# 10) CheckConstraint cu Q: minimum 5 constrângeri la nivel de bază de date.
# 11) db_index=True: câmpuri folosite frecvent la căutare/filtrare.
# 12) ImageField: imaginea produsului.


class Categorie(models.Model):
    # L3  1.2: nume, descriere, culoare și siglă sunt atribute obligatorii în diagramă.
    # L3  1.1,  1.2: numele este unic; descrierea poate fi NULL.
    nume = models.CharField(max_length=60, unique=True,
        error_messages={"unique": "Categoria există deja.", "max_length": "Numele este prea lung."})
    slug = models.SlugField(max_length=70, unique=True,
        help_text="Adresă scurtă folosită în URL.",
        error_messages={"unique": "Slug-ul categoriei trebuie să fie unic.", "max_length": "Slug-ul este prea lung."})
    descriere = models.TextField(null=True, blank=True, help_text="Descrierea categoriei.")
    culoare = models.CharField(max_length=7, default="#6B2E1F", blank=True,
        help_text="Culoare HEX, de exemplu #6B2E1F.")
    sigla = models.CharField(max_length=50, default="fa-cookie-bite", blank=True,
        help_text="Numele unei pictograme sau calea unei imagini.")
    ordine = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        # L3  1.4: ordonare implicită; T1.10: constrângere Q.
        ordering = ["ordine", "nume"]
        verbose_name = "categorie"
        verbose_name_plural = "categorii"
        constraints = [models.CheckConstraint(condition=Q(ordine__gte=0), name="categorie_ordine_min_zero")]

    def __str__(self):
        return self.nume


class Brand(models.Model):
    nume = models.CharField(max_length=80, unique=True,
        error_messages={"unique": "Acest brand există deja.", "max_length": "Numele brandului este prea lung."})
    # L3  1.1: câmpuri care admit NULL; T1.3: URLField.
    tara_origine = models.CharField(max_length=50, null=True, blank=True)
    site_web = models.URLField(null=True, blank=True, help_text="Site-ul oficial al brandului.",
        error_messages={"invalid": "Introduceți o adresă URL validă."})

    class Meta:
        # L3  1.4: ordonare implicită pentru al doilea model.
        ordering = ["nume"]
        verbose_name = "brand"
        verbose_name_plural = "branduri"

    def __str__(self):
        return self.nume


class Ambalaj(models.Model):
    # L3  1.5: choices (text cu valori permise) pentru material.
    class Material(models.TextChoices):
        CARTON = "carton", "Carton"
        STICLA = "sticla", "Sticlă"
        METAL = "metal", "Metal"
        PLASTIC = "plastic", "Plastic"
        TEXTIL = "textil", "Textil"

    material = models.CharField(max_length=20, choices=Material.choices, default=Material.CARTON)
    nume = models.CharField(max_length=60, unique=True,
        error_messages={"unique": "Acest ambalaj există deja."})
    # L3  1.6 și  1.9: default, validator și mesaj de eroare.
    capacitate_buc = models.PositiveIntegerField(default=1,
        validators=[MinValueValidator(1, message="Capacitatea trebuie să fie cel puțin 1.")],
        error_messages={"invalid": "Introduceți un număr întreg."})
    reciclabil = models.BooleanField(default=True)

    class Meta:
        ordering = ["nume"]
        verbose_name = "ambalaj"
        verbose_name_plural = "ambalaje"
        # L3  1.10: constrângere models.Q.
        constraints = [models.CheckConstraint(condition=Q(capacitate_buc__gt=0), name="ambalaj_capacitate_pozitiva")]

    def __str__(self):
        return self.nume


class Ingredient(models.Model):
    nume = models.CharField(max_length=80, unique=True,
        error_messages={"unique": "Ingredientul există deja.", "max_length": "Numele ingredientului este prea lung."})
    # L3  1.1: origine poate fi NULL; T1.7: help_text relevant.
    origine = models.CharField(max_length=80, null=True, blank=True,
        help_text="Țara sau regiunea de proveniență.")
    certificat_bio = models.BooleanField(default=False)

    class Meta:
        ordering = ["nume"]
        verbose_name = "ingredient"
        verbose_name_plural = "ingrediente"

    def __str__(self):
        return self.nume


class SediuCompanie(models.Model):
    nume = models.CharField(max_length=80, unique=True)
    adresa = models.CharField(max_length=180, help_text="Adresa completă a sediului.",
        error_messages={"max_length": "Adresa este prea lungă."})
    telefon = models.CharField(max_length=20, help_text="Număr de telefon pentru sediu.",
        error_messages={"max_length": "Numărul de telefon este prea lung."})
    # L3  1.1 și  1.3: email opțional și EmailField.
    email = models.EmailField(null=True, blank=True,
        error_messages={"invalid": "Introduceți o adresă de email validă."})
    sediu_principal = models.BooleanField(default=False)

    class Meta:
        verbose_name = "sediu"
        verbose_name_plural = "sedii"

    def __str__(self):
        return self.nume


class Produs(models.Model):
    # L3  1.5: choices pentru tipul produsului.
    class Tip(models.TextChoices):
        TABLETA = "tableta", "Tabletă"
        PRALINE = "praline", "Praline"
        TRUFE = "trufe", "Trufe"
        CREMA = "crema", "Cremă"
        CADOU = "cadou", "Pachet cadou"

    # L3  1.1,  1.2 și  1.9: produs cu câmpuri opționale, nume unic și erori explicite.
    nume = models.CharField(max_length=100, unique=True,
        error_messages={"unique": "Există deja un produs cu acest nume.", "max_length": "Numele produsului este prea lung."})
    # L3  1.3: SlugField; 1.9: mesaj personalizat pentru unicitate și lungime.
    slug = models.SlugField(max_length=110, unique=True,
        error_messages={"unique": "Adresa produsului trebuie să fie unică.", "max_length": "Adresa produsului este prea lungă."})
    descriere = models.TextField(null=True, blank=True)
    # L3  1.9: mesaj pentru preț invalid și limite numerice.
    pret = models.DecimalField(max_digits=8, decimal_places=2,
        validators=[MinValueValidator(0.01, message="Prețul trebuie să fie mai mare decât 0.")],
        error_messages={"invalid": "Introduceți un preț valid.", "max_digits": "Prețul are prea multe cifre."})
    gramaj_g = models.PositiveIntegerField(default=100,
        validators=[MinValueValidator(1, message="Gramajul trebuie să fie pozitiv.")],
        error_messages={"invalid": "Gramajul trebuie să fie un număr întreg."})
    # L3  1.1: poate fi NULL; T1.9: mesaje pentru intervalul 0-100.
    procent_cacao = models.FloatField(null=True, blank=True,
        validators=[MinValueValidator(0, message="Procentul nu poate fi negativ."),
                    MaxValueValidator(100, message="Procentul nu poate depăși 100.")],
        error_messages={"invalid": "Introduceți un procent numeric valid."})
    tip = models.CharField(max_length=20, choices=Tip.choices, default=Tip.TABLETA, db_index=True)
    disponibil = models.BooleanField(default=True, db_index=True)
    # L3  1.6 și  1.7: default list (apelabil), blank=True și help_text.
    # L3  3.6: atribut cu valori multiple (vector), excepția permisă de cerință față de 1NF.
    arome = models.JSONField(default=list, blank=True,
        help_text='Listă de arome, de exemplu: ["vanilie", "portocală"].')
    # L3  1.12: imagine salvată în MEDIA_ROOT/produse/; Pillow este în requirements.txt.
    imagine = models.ImageField(upload_to="produse/", null=True, blank=True)
    # L3  1.8 și  1.11: data implicită este momentul creării, câmp indexat.
    data_adaugare = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    # L3  3.4: relații 1:N către produs din categorie, brand și ambalaj.
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name="produse")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="produse")
    ambalaj = models.ForeignKey(Ambalaj, on_delete=models.PROTECT, related_name="produse")
    # L3  3.5: relație M:N Produs–Ingredient.
    ingrediente = models.ManyToManyField(Ingredient, related_name="produse", blank=True)

    class Meta:
        # L3  1.4: ordonare implicită; plural corect în Admin.
        ordering = ["nume"]
        verbose_name = "produs"
        verbose_name_plural = "produse"
        # L3  1.10: trei constrângeri cu models.Q.
        constraints = [
            models.CheckConstraint(condition=Q(pret__gt=0), name="produs_pret_pozitiv"),
            models.CheckConstraint(condition=Q(gramaj_g__gt=0), name="produs_gramaj_pozitiv"),
            models.CheckConstraint(condition=Q(procent_cacao__isnull=True) | (Q(procent_cacao__gte=0) & Q(procent_cacao__lte=100)), name="produs_cacao_0_100"),
        ]

    def __str__(self):
        return self.nume


class LotProductie(models.Model):
    # L3  3.9: entitate slabă dependentă de Produs.
    produs = models.ForeignKey(Produs, on_delete=models.CASCADE, related_name="loturi")
    # nr_lot singur nu este unic; perechea produs + nr_lot identifică lotul.
    nr_lot = models.PositiveIntegerField()
    sediu = models.ForeignKey(SediuCompanie, on_delete=models.PROTECT, related_name="loturi")
    data_productie = models.DateField(default=timezone.localdate)
    data_expirare = models.DateField()
    cantitate = models.PositiveIntegerField(default=1,
        validators=[MinValueValidator(1, message="Cantitatea trebuie să fie cel puțin 1.")],
        error_messages={"invalid": "Cantitatea trebuie să fie un număr întreg."})

    class Meta:
        ordering = ["-data_productie"]
        verbose_name = "lot de producție"
        verbose_name_plural = "loturi de producție"
        # L3  3.9: cheia logică a entității slabe este produs + nr_lot.
        # L3 1.10: constrângere unică și două CheckConstraint cu Q/F.
        constraints = [
            models.UniqueConstraint(fields=["produs", "nr_lot"], name="lot_produs_nr_unic"),
            models.CheckConstraint(condition=Q(cantitate__gt=0), name="lot_cantitate_pozitiva"),
            models.CheckConstraint(condition=Q(data_expirare__gte=F("data_productie")), name="lot_expirare_dupa_productie"),
        ]

    def __str__(self):
        return f"Lot {self.nr_lot} - {self.produs.nume}"
