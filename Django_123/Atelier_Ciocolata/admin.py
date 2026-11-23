from django.contrib import admin
from .models import Categorie, Brand, Ambalaj, Ingredient, SediuCompanie, Produs, LotProductie

# LAB 3, TASK 2: înregistrăm toate modelele și definim listări utile în Admin.


class LotInline(admin.TabularInline):
    model = LotProductie
    extra = 0


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    # Afișare relevantă pentru categorii; slug-ul se generează din nume.
    list_display = ("nume", "slug", "culoare", "ordine")
    search_fields = ("nume",)
    prepopulated_fields = {"slug": ("nume",)}


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("nume", "tara_origine", "site_web")
    search_fields = ("nume", "tara_origine")


@admin.register(Ambalaj)
class AmbalajAdmin(admin.ModelAdmin):
    list_display = ("nume", "material", "capacitate_buc", "reciclabil")
    list_filter = ("material", "reciclabil")
    search_fields = ("nume",)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("nume", "origine", "certificat_bio")
    list_filter = ("certificat_bio",)
    search_fields = ("nume", "origine")


@admin.register(SediuCompanie)
class SediuAdmin(admin.ModelAdmin):
    list_display = ("nume", "adresa", "telefon", "email", "sediu_principal")
    list_filter = ("sediu_principal",)
    search_fields = ("nume", "adresa", "telefon")
    inlines = (LotInline,)


@admin.register(Produs)
class ProdusAdmin(admin.ModelAdmin):
    # Cel puțin 10 produse pot fi introduse și gestionate în interfața /admin/.
    list_display = ("nume", "categorie", "brand", "pret", "tip", "disponibil", "data_adaugare")
    list_filter = ("categorie", "brand", "tip", "disponibil")
    search_fields = ("nume", "slug", "descriere")
    prepopulated_fields = {"slug": ("nume",)}
    filter_horizontal = ("ingrediente",)
    readonly_fields = ("data_adaugare",)
    list_select_related = ("categorie", "brand", "ambalaj")
    inlines = (LotInline,)


@admin.register(LotProductie)
class LotAdmin(admin.ModelAdmin):
    list_display = ("nr_lot", "produs", "sediu", "data_productie", "data_expirare", "cantitate")
    list_filter = ("data_productie", "sediu")
    search_fields = ("produs__nume", "sediu__nume")
    list_select_related = ("produs", "sediu")
