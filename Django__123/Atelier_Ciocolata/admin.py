from django.contrib import admin
from .models import (
    Organizator, SediuEveniment, Ambalaj, Categorie,
    Prajitura, Eveniment, PrajituriEvenimente, IstoricPret )


@admin.register(Organizator)
class OrganizatorAdmin(admin.ModelAdmin):
    list_display = ('nume', 'email', 'activ')


@admin.register(SediuEveniment)
class SediuEvenimentAdmin(admin.ModelAdmin):
    list_display = ('nume', 'oras', 'judet')


@admin.register(Ambalaj)
class AmbalajAdmin(admin.ModelAdmin):
    list_display = ('nume', 'culoare', 'nivel_rezistenta')


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'culoare', 'ordine')


@admin.register(Prajitura)
class PrajituraAdmin(admin.ModelAdmin):
    list_display = ('nume', 'categorie', 'pret', 'gramaj', 'stoc')


@admin.register(Eveniment)
class EvenimentAdmin(admin.ModelAdmin):
    list_display = ('titlu', 'tip_eveniment', 'sediu', 'organizator')


@admin.register(PrajituriEvenimente)
class PrajituriEvenimenteAdmin(admin.ModelAdmin):
    list_display = ('prajitura', 'eveniment', 'nr_prajituri')


@admin.register(IstoricPret)
class IstoricPretAdmin(admin.ModelAdmin):
    list_display = ('produs', 'pret', 'data_pret_nou')
