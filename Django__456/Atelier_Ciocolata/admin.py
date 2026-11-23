import csv
from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils.html import format_html
from .models import (Organizator, SediuEveniment, Ambalaj, Categorie,
                     Prajitura, Eveniment, PrajituriEvenimente, IstoricPret,
                     Departament, TipMesaj, TipMesajDepartament)


# Lab 4 – 10: prima acțiune Admin, export CSV.
@admin.action(description='Exportă produsele selectate în CSV')
def export_csv(modeladmin, request, queryset):
    raspuns = HttpResponse(content_type='text/csv; charset=utf-8')
    raspuns['Content-Disposition'] = 'attachment; filename="prajituri.csv"'
    raspuns.write('\ufeff')
    writer = csv.writer(raspuns)
    writer.writerow(['Nume', 'Categorie', 'Preț', 'Stoc'])
    for produs in queryset:
        writer.writerow([produs.nume, produs.categorie.nume, produs.pret, produs.stoc])
    return raspuns


# Lab 4 –  10: a doua acțiune Admin, actualizare stoc.
@admin.action(description='Marchează produsele selectate ca stoc limitat')
def stoc_limitat(modeladmin, request, queryset):
    numar = queryset.update(stoc=2)
    modeladmin.message_user(request, f'{numar} produse au acum stocul 2.', messages.SUCCESS)


# Lab 4 –  6: toate tabelele Admin afișează câte 5 rânduri/pagină.
class AdminSimplu(admin.ModelAdmin):
    list_per_page = 5


# Lab 4 – configurații de listare și căutare pentru celelalte modele.
@admin.register(Organizator)
class OrganizatorAdmin(AdminSimplu):
    list_display = ('nume', 'email', 'activ')
    search_fields = ('nume', 'email')
    search_help_text = 'Caută după numele organizatorului sau adresa de email.'
    list_filter = ('activ', 'vip', 'persoana_juridica')


@admin.register(SediuEveniment)
class SediuEvenimentAdmin(AdminSimplu):
    list_display = ('nume', 'oras', 'judet', 'adresa')
    search_fields = ('nume', 'oras')
    search_help_text = 'Caută după numele sediului sau oraș.'


@admin.register(Ambalaj)
class AmbalajAdmin(AdminSimplu):
    list_display = ('nume', 'culoare', 'nivel_rezistenta')
    search_fields = ('nume', 'culoare')
    search_help_text = 'Caută după numele ambalajului sau culoare.'


# Lab 4 – CERINȚELE 1 și 3 pentru modelul Categorie.
@admin.register(Categorie)
class CategorieAdmin(AdminSimplu):
    list_display = ('nume', 'culoare', 'ordine', 'numar_produse')
    search_fields = ('nume', 'descriere')
    search_help_text = 'Caută după numele sau descrierea categoriei.'
    ordering = ('ordine', 'nume')

    @admin.display(description='Produse')
    def numar_produse(self, obj):
        return obj.prajituri.count()


# Lab 4 – CERINȚELE 1–7 și 10 pentru modelul Prajitura.
@admin.register(Prajitura)
class PrajituraAdmin(AdminSimplu):
    # 1: ordinea coloanelor este personalizată; nume_categorie arată relația cu Categorie.
    list_display = ('nume', 'categorie', 'pret_formatat', 'gramaj', 'stoc', 'nume_categorie')
    list_display_links = ('nume',)
    # 3: căutare în două câmpuri și explicație pentru utilizator.
    search_fields = ('nume', 'descriere')
    search_help_text = 'Caută după numele sau descrierea prăjiturii.'
    # 5: filtre laterale după categorie, tip și produse pentru diabetici.
    list_filter = ('categorie', 'tip_produs', 'pt_diabetici')
    # 4: produsele sunt ordonate crescător după preț în Admin.
    ordering = ('pret',)
    # 10: cele două acțiuni definite mai sus.
    actions = (export_csv, stoc_limitat)
    # 7: formularul este împărțit în două secțiuni; a doua este colapsabilă.
    # Secțiunea colapsabilă conține doar detalii opționale.
    fieldsets = (
        ('Date principale', {'fields': ('nume', 'descriere', 'pret', 'categorie', 'tip_produs', 'gramaj', 'calorii', 'stoc', 'stoc_rezervat')}),
        ('Detalii opționale', {'classes': ('collapse',), 'fields': ('imagine', 'ingrediente', 'taguri', 'ambalaje', 'pt_diabetici')}),
    )

    # 2: @admin.display + format_html formatează prețul cu text îngroșat și colorat.
    @admin.display(description='Preț', ordering='pret')
    def pret_formatat(self, obj):
        return format_html('<strong style="color:#9b2450">{} lei</strong>', obj.pret)

    @admin.display(description='Categorie')
    def nume_categorie(self, obj):
        return format_html('<em>{}</em>', obj.categorie.nume)


@admin.register(Eveniment)
class EvenimentAdmin(AdminSimplu):
    list_display = ('titlu', 'tip_eveniment', 'sediu', 'organizator')
    search_fields = ('titlu', 'descriere')
    search_help_text = 'Caută după titlul sau descrierea evenimentului.'
    list_filter = ('tip_eveniment', 'este_public')


@admin.register(PrajituriEvenimente)
class PrajituriEvenimenteAdmin(AdminSimplu):
    list_display = ('prajitura', 'eveniment', 'nr_prajituri')
    search_fields = ('prajitura__nume', 'eveniment__titlu')
    search_help_text = 'Caută după numele prăjiturii sau titlul evenimentului.'


@admin.register(IstoricPret)
class IstoricPretAdmin(AdminSimplu):
    list_display = ('produs', 'pret', 'data_pret_nou')
    search_fields = ('produs__nume', 'produs__descriere')
    search_help_text = 'Caută după numele sau descrierea produsului.'
    ordering = ('-data_pret_nou',)


# Lab 4 – CERINȚA 8: textele din antet, titlu și linkul View site.
admin.site.site_header = 'Atelier de Ciocolată | Administrare'
admin.site.site_title = 'Administrare Atelier de Ciocolată'
admin.site.index_title = 'Panou de administrare'
admin.site.site_url = '/'


@admin.register(Departament)
class DepartamentAdmin(AdminSimplu):
    list_display = ('nume', 'slug')
    search_fields = ('nume', 'slug')
    search_help_text = 'Caută după numele sau identificatorul departamentului.'


@admin.register(TipMesaj)
class TipMesajAdmin(AdminSimplu):
    list_display = ('nume', 'minim_zile')
    search_fields = ('nume',)
    search_help_text = 'Caută după numele tipului de mesaj.'


@admin.register(TipMesajDepartament)
class TipMesajDepartamentAdmin(AdminSimplu):
    list_display = ('tip_mesaj', 'departament')
    search_fields = ('tip_mesaj__nume', 'departament__nume')
    search_help_text = 'Caută după tipul mesajului sau departament.'
