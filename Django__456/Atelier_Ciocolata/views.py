from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
import html
import json
import re
import secrets
import string

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.utils.text import slugify

from .models import Prajitura, Categorie, TipMesaj, Departament
from .forms import FiltruProduseForm, ContactForm, AdaugaPrajituraForm
from .utils import varsta_ani_luni

DESCRIERE = 'Atelierul de ciocolată este un magazin de prăjituri și produse de cofetărie pe bază de ciocolată.'
ZILE = ('Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică')
LUNI = ('Ianuarie', 'Februarie', 'Martie', 'Aprilie', 'Mai', 'Iunie', 'Iulie',
        'August', 'Septembrie', 'Octombrie', 'Noiembrie', 'Decembrie')
FORMAT_DATA = '%A, %-d %B %Y'
MESAJE_DIR = Path(__file__).resolve().parent / 'Mesaje_nerezolvate'

# Parametrii din URL care NU sunt filtre (folosiți pentru mesajul "filtre aplicate").
PARAMETRI_NEFILTRU = {'camp', 'sort', 'page', 'per_page', 'coloane', 'tag', 'reset'}

# LAB 5 – TASK 2: câmp din formular -> condiție ORM (se aplică dacă valoarea e completată).
FILTRE_SIMPLE = {
    'id': 'pk',
    'nume': 'nume__icontains',
    'descriere': 'descriere__icontains',
    'tip_produs': 'tip_produs',
    'ambalaj': 'ambalaje',
    'data_de_la': 'data_creare__date__gte',
    'data_pana_la': 'data_creare__date__lte',
    'pret_min': 'pret__gte', 'pret_max': 'pret__lte',
    'gramaj_min': 'gramaj__gte', 'gramaj_max': 'gramaj__lte',
    'calorii_min': 'calorii__gte', 'calorii_max': 'calorii__lte',
    'stoc_min': 'stoc__gte', 'stoc_max': 'stoc__lte',
    'stoc_rezervat_min': 'stoc_rezervat__gte', 'stoc_rezervat_max': 'stoc_rezervat__lte',
}


class Accesare:
    urmatorul_id = 1

    def __init__(self, ip_client, url, parametri=None, data=None):
        self.id = Accesare.urmatorul_id
        Accesare.urmatorul_id += 1
        self.ip_client = ip_client
        self.url = url
        self.parametri = parametri or {}
        self.data = data or datetime.now()

    def lista_parametri(self):
        return [(nume, valoare if valoare != '' else None) for nume, valoare in self.parametri.items()]

    def string_url(self):
        return self.url

    def pagina(self):
        return urlsplit(self.url).path

    def calculeaza_data(self, format=FORMAT_DATA, tip=''):
        format_implicit = format == FORMAT_DATA and not tip
        if tip == 'zi':
            format = '%-d %B %Y'
        elif tip == 'timp':
            format = '%H:%M:%S'
        # Înlocuim numele zilelor/lunilor cu varianta în română.
        zi, luna = ZILE[self.data.weekday()], LUNI[self.data.month - 1]
        for cod, text in (('%A', zi), ('%a', zi[:3]), ('%B', luna), ('%b', luna[:3]), ('%-d', str(self.data.day))):
            format = format.replace(cod, text)
        valoare = self.data.strftime(format)
        if format_implicit:
            valoare += ' ' + self.data.strftime('%H:%M:%S')
        return f'<section><h2>Data și ora</h2><p>{valoare}</p></section>'

    def __str__(self):
        return (f'id: {self.id}\nip_client: {self.ip_client}\nstring_url: {self.string_url()}\n'
                f'pagina: {self.pagina()}\ncalculeaza_data: {self.calculeaza_data()}\n'
                f'lista_parametri: {self.lista_parametri()}')


accesari = []

def index(request):
    return render(request, 'Atelier_Ciocolata/index.html', {'descriere': DESCRIERE})

def info(request):
    sectiune = request.accesare.calculeaza_data(tip=request.GET.get('data', ''))
    return render(request, 'Atelier_Ciocolata/info.html', {'sectiune': sectiune})

def despre(request):
    return render(request, 'Atelier_Ciocolata/despre.html')

def istoric(request):
    return render(request, 'Atelier_Ciocolata/istoric.html')

def in_lucru(request):
    return render(request, 'Atelier_Ciocolata/in_lucru.html')


# ============================================================
# QUERYSETS – CERINȚELE 1–10
# 1: toate produsele; 3: sortare; 4–5: stoc și taguri; 6: Paginator;
# 7 și 10: reutilizarea aceleiași pagini pentru o categorie.
# LAB 5 – TASK 2: filtrele din FiltruProduseForm se aplică aici.
# ============================================================
def aplica_filtre(produse, date_filtre, categorie_curenta):
    """LAB 5 Task 2.2 și 2.5: aplică filtrele formularului (se apelează doar după is_valid)."""
    # Un singur filter() pentru toate condițiile simple (text, numere, date, alegeri).
    conditii = {
        cautare: date_filtre[camp]
        for camp, cautare in FILTRE_SIMPLE.items()
        if date_filtre.get(camp) not in (None, '')
    }
    if date_filtre.get('categorie') and not categorie_curenta:
        conditii['categorie'] = date_filtre['categorie']
    if date_filtre.get('pt_diabetici') in ('da', 'nu'):
        conditii['pt_diabetici'] = date_filtre['pt_diabetici'] == 'da'
    if date_filtre.get('ingredient'):
        conditii['ingrediente__contains'] = [date_filtre['ingredient']]
    if date_filtre.get('tag_cautat'):
        conditii['taguri__contains'] = [date_filtre['tag_cautat']]
    produse = produse.filter(**conditii)

    if date_filtre.get('imagine') == 'da':
        produse = produse.exclude(imagine='').exclude(imagine__isnull=True)
    elif date_filtre.get('imagine') == 'nu':
        produse = produse.filter(Q(imagine='') | Q(imagine__isnull=True))
    return produse


def construieste_url_taguri(request, taguri):
    """Pentru fiecare tag: URL-ul care îl adaugă sau îl scoate din filtrele active."""
    baza = request.GET.copy()
    baza.pop('page', None)
    baza.pop('reset', None)
    urluri = {}
    for tag in taguri:
        parametri = baza.copy()
        valori = parametri.getlist('tag')
        if tag in valori:
            valori.remove(tag)
        else:
            valori.append(tag)
        parametri.setlist('tag', valori)
        urluri[tag] = '?' + parametri.urlencode()
    return urluri


def produse(request, categorie=None):
    # QuerySets 7 și 10: dacă URL-ul conține o categorie, o găsim în baza de date.
    categorie_curenta = get_object_or_404(Categorie, nume__iexact=categorie) if categorie is not None else None

    if request.GET.get('reset') == '1':
        messages.warning(request, 'Filtrele au fost resetate. Se vor afișa din nou produsele disponibile.')
        if categorie_curenta:
            return redirect('categorie_produse', nume_categorie=categorie_curenta.nume)
        return redirect('produse')

    date_formular = None
    if request.GET:
        date_formular = request.GET.copy()
        date_formular.setdefault('per_page', str(settings.PROD_PER_PAG))
        date_formular.setdefault('coloane', '3')
        if categorie_curenta and 'categorie' not in date_formular:
            date_formular['categorie'] = categorie_curenta.pk

    # QuerySets 1: selectăm toate produsele; select_related/prefetch_related încarcă relațiile eficient.
    # LAB 5 Task 2: același formular de filtrare este folosit și pentru listă și pentru categorie.
    formular = FiltruProduseForm(date_formular, categorie_fixa=categorie_curenta)
    produse_qs = Prajitura.objects.select_related('categorie').prefetch_related('ambalaje')
    if categorie_curenta:
        produse_qs = produse_qs.filter(categorie=categorie_curenta)

    formular_valid = formular.is_valid()
    if formular_valid:
        produse_qs = aplica_filtre(produse_qs, formular.cleaned_data, categorie_curenta)
    elif request.GET:
        messages.error(request, 'Unele filtre nu sunt valide. Verifică mesajele afișate lângă câmpuri.')

    # QuerySets 4–5: pentru mai multe taguri folosim filter() repetat (condiție AND).
    # Produsul trebuie să conțină toate tagurile active.
    taguri_active = request.GET.getlist('tag')
    for tag in taguri_active:
        produse_qs = produse_qs.filter(taguri__contains=[tag])

    # QuerySets 3: sortare doar după coloanele permise; a = crescător, d = descrescător.
    coloana = request.GET.get('camp', 'nume')
    if coloana not in ('nume', 'pret', 'gramaj', 'stoc'):
        coloana = 'nume'
    sens = request.GET.get('sort', 'a')
    if sens not in ('a', 'd'):
        sens = 'a'
    produse_qs = produse_qs.order_by(('-' if sens == 'd' else '') + coloana, 'pk')

    per_page, coloane = settings.PROD_PER_PAG, 3
    if formular_valid:
        per_page = int(formular.cleaned_data.get('per_page') or 6)
        coloane = int(formular.cleaned_data.get('coloane') or 3)
    per_page_vechi = request.session.get('ultima_paginare')
    if per_page_vechi and int(per_page_vechi) != per_page:
        messages.warning(request, 'Ai schimbat numărul de produse pe pagină. Este posibil să revezi produse sau să sari peste unele deja văzute.')
    request.session['ultima_paginare'] = per_page

    # QuerySets 6 și LAB 5 Task 2.7–2.8: paginarea are loc după filtrare și sortare.
    # Astfel, pagina următoare păstrează ordinea și criteriile selectate.
    paginator = Paginator(produse_qs, per_page)
    pagina = paginator.get_page(request.GET.get('page'))
    inceput = (pagina.number - 1) * per_page + 1 if pagina.object_list else 0
    sfarsit = inceput + len(pagina.object_list) - 1

    query = request.GET.copy()
    query.pop('page', None)
    query.pop('reset', None)

    # QuerySets 5 și 8: tagurile disponibile și meniul de categorii se bazează pe datele DB.
    sursa_taguri = Prajitura.objects.all()
    if categorie_curenta:
        sursa_taguri = sursa_taguri.filter(categorie=categorie_curenta)
    taguri_disponibile = sorted({tag for lista in sursa_taguri.values_list('taguri', flat=True) for tag in (lista or [])})
    tag_urluri = construieste_url_taguri(request, set(taguri_active) | set(taguri_disponibile))

    messages.debug(request, 'A fost încărcată lista de produse.')
    if formular_valid and set(request.GET) - PARAMETRI_NEFILTRU:
        messages.info(request, 'Filtrele produselor au fost aplicate.')
    if paginator.count == 0:
        messages.info(request, 'Nu există produse care să corespundă criteriilor selectate.')

    return render(request, 'Atelier_Ciocolata/produse.html', {
        'pagina': pagina, 'produse': pagina.object_list, 'filtru': formular,
        'categorie_curenta': categorie_curenta,
        # QuerySets 8: în meniu trimitem numai categorii care au produse.
        'categorii': Categorie.objects.filter(prajituri__isnull=False).distinct(),
        'taguri_active': taguri_active, 'toate_tagurile': taguri_disponibile,
        'coloana': coloana, 'sens': sens, 'query_string': query.urlencode(),
        'tag_urluri': tag_urluri, 'inceput': inceput, 'sfarsit': sfarsit,
        'total': paginator.count, 'stoc_min': settings.STOC_MIN,
        'coloane': coloane, 'per_page': per_page,
    })


# QuerySets 2: detalii produs; get_object_or_404 afișează 404 dacă ID-ul nu există.
def produs_detaliu(request, pk):
    messages.debug(request, 'A fost deschisă pagina detaliată a unui produs.')
    produs = get_object_or_404(Prajitura.objects.select_related('categorie').prefetch_related('ambalaje'), pk=pk)
    # QuerySets 2: alegem aleatoriu maximum 4 produse din aceeași categorie.
    similare = Prajitura.objects.filter(categorie=produs.categorie).exclude(pk=produs.pk).order_by('?')[:4]
    return render(request, 'Atelier_Ciocolata/produs_detaliu.html', {
        'produs': produs, 'similare': similare, 'stoc_min': settings.STOC_MIN,
    })


# QuerySets 7 și 10: pagina categoriei reutilizează view-ul și template-ul produselor.
def categorie_produse(request, nume_categorie):
    return produse(request, categorie=nume_categorie)


def selecteaza_dupa_id(request):
    """Parametrii ?iduri=1,2,3 și ?dubluri=true."""
    iduri = [parte.strip() for text in request.GET.getlist('iduri') for parte in text.split(',')]
    dictionar = {a.id: a for a in accesari}
    dubluri = request.GET.get('dubluri', 'false').lower() == 'true'
    selectie, folosite = [], set()
    for valoare in iduri:
        if valoare.isascii() and valoare.isdecimal():
            identificator = int(valoare)
            if identificator in dictionar and (dubluri or identificator not in folosite):
                selectie.append(dictionar[identificator])
                folosite.add(identificator)
    return selectie


def log(request):
    selectie = selecteaza_dupa_id(request) if 'iduri' in request.GET else list(accesari)
    eroare = ''
    if 'ultimele' in request.GET:
        text = request.GET['ultimele']
        if not (text.isascii() and text.isdecimal()):
            eroare = 'Parametrul ultimele trebuie să fie un număr întreg nenegativ.'
            selectie = []
        else:
            numar = int(text)
            if numar > len(selectie):
                eroare = f'Exista doar {len(selectie)} accesari fata de {numar} accesari cerute'
            selectie = selectie[-numar:] if numar else []

    mod = request.GET.get('accesari')
    toate_coloanele = ('id', 'ip_client', 'url', 'parametri', 'data')
    tabel = request.GET.get('tabel')
    coloane, randuri = [], []
    if tabel is not None:
        coloane = list(toate_coloanele) if tabel == 'tot' else [c for c in tabel.split(',') if c in toate_coloanele]
        randuri = [[str(getattr(a, camp)) for camp in coloane] for a in selectie]

    frecventa = Counter(a.pagina() for a in accesari)
    parametri = [cheie for cheie, valori in request.GET.lists() for _ in valori]
    return render(request, 'Atelier_Ciocolata/log.html', {
        'accesari': selectie, 'eroare': eroare,
        'numar_accesari': len(accesari) if mod == 'nr' else None,
        'detalii': selectie if mod == 'detalii' else None,
        'coloane': coloane, 'randuri': randuri, 'tabel': tabel is not None,
        'numar_parametri': len(parametri), 'parametri': parametri,
        'pagina_minima': min(frecventa, key=frecventa.get) if frecventa else None,
        'pagina_maxima': max(frecventa, key=frecventa.get) if frecventa else None,
    })


def detalii_accesare(request, id):
    accesare = next((a for a in accesari if a.id == int(id)), None)
    if accesare is None:
        raise Http404('Accesarea nu există.')
    return render(request, 'Atelier_Ciocolata/accesare.html', {'accesare': accesare})


def cod_nou_cerere():
    """Cod: 3 litere mari, 2 mici și 8 cifre aleatoare."""
    def alege(alfabet, n):
        return ''.join(secrets.choice(alfabet) for _ in range(n))
    return alege(string.ascii_uppercase, 3) + alege(string.ascii_lowercase, 2) + alege(string.digits, 8)


def calculeaza_varsta(data_nasterii):
    ani, luni = varsta_ani_luni(data_nasterii)
    return f'{ani} ani și {luni} luni'


def mesaj_html(text):
    """Transformă fiecare rând în paragraf și normalizează spațiile."""
    randuri = []
    for rand in text.replace('\r', '').split('\n'):
        rand = re.sub(r'\s+', ' ', rand).strip()
        if rand:
            rand = re.sub(r'([.!?]+)\s+([a-zăâîșț])', lambda m: m.group(1) + ' ' + m.group(2).upper(), rand)
            randuri.append(f'<p>{html.escape(rand)}</p>')
    return ''.join(randuri)


def salveaza_imagini(date_form, departament, timestamp):
    """Salvează cele 3 atașamente opționale în MEDIA_ROOT și întoarce căile relative."""
    folder_media = Path(settings.MEDIA_ROOT) / 'Mesaje_nerezolvate' / departament.slug
    folder_media.mkdir(parents=True, exist_ok=True)
    imagini = {}
    for index in range(1, 4):
        imagine = date_form.get(f'imagine{index}')
        cale_relativa = ''
        if imagine:
            extensie = Path(imagine.name).suffix.lower() or '.img'
            nume_imagine = f'atasament_{index}_{timestamp}{extensie}'
            with open(folder_media / nume_imagine, 'wb') as fisier:
                for bucata in imagine.chunks():
                    fisier.write(bucata)
            cale_relativa = f'Mesaje_nerezolvate/{departament.slug}/{nume_imagine}'
        imagini[f'imagine{index}'] = cale_relativa
    return imagini


# LABORATORUL 5 – TASK 3: primim formularul Contact și salvăm datele în JSON.
# Nu folosim un model pentru mesajul complet.
def contact(request):
    if request.method == 'POST':
        formular = ContactForm(request.POST, request.FILES)
        if formular.is_valid():
            date_form = formular.cleaned_data
            tip = date_form['tip_mesaj']
            departament = date_form['departament']
            # Task 3.4: mesajul este urgent dacă zilele alese sunt chiar minimul permis.
            urgent = date_form['minim_zile'] == tip.minim_zile
            acum = timezone.now()
            timestamp = int(acum.timestamp())

            # Folderul departamentului (doar cel ales; celelalte se creează când e nevoie).
            folder_departament = MESAJE_DIR / departament.slug
            folder_departament.mkdir(parents=True, exist_ok=True)

            # Task 3.4–3.5: pregătim toate datele și le scriem într-un fișier JSON.
            # Confirmarea e-mailului și data nașterii nu se salvează; păstrăm vârsta.
            continut = {
                'nume': date_form['nume'],
                'prenume': date_form.get('prenume', ''),
                'cnp': date_form.get('cnp', ''),
                'varsta': calculeaza_varsta(date_form['data_nasterii']),
                'email': date_form['email'],
                'telefon': date_form.get('telefon', ''),
                'tip_mesaj': tip.nume,
                'departament': departament.nume,
                'subiect': date_form['subiect'],
                'minim_zile': date_form['minim_zile'],
                'mesaj': mesaj_html(date_form['mesaj']),
                **salveaza_imagini(date_form, departament, timestamp),
                'gdpr': date_form['gdpr'],
                'cod_cerere': date_form['cod_cerere'],
                'urgent': urgent,
                'ip': getattr(request, 'ip_client', request.META.get('REMOTE_ADDR', '')),
                'data_ora': timezone.localtime(acum).isoformat(),
            }
            # Task 3.5: numele fișierului conține timestamp și, când este cazul, _urgent.
            sufix = '_urgent' if urgent else ''
            cale_json = folder_departament / f'mesaj_{timestamp}{sufix}.json'
            with open(cale_json, 'w', encoding='utf-8') as fisier:
                json.dump(continut, fisier, ensure_ascii=False, indent=2)

            messages.success(request, f'Mesajul a fost trimis. Codul cererii este {date_form["cod_cerere"]}.')
            return redirect('contact')
        messages.error(request, 'Formularul conține erori. Corectează câmpurile marcate.')
    else:
        formular = ContactForm(initial={'cod_cerere': cod_nou_cerere()})
        messages.info(request, 'Completează formularul de contact. Câmpurile marcate cu * sunt obligatorii.')
    messages.debug(request, 'Pagina de contact a fost accesată.')
    return render(request, 'Atelier_Ciocolata/contact.html', {'formular': formular})


# Task 3.1.7: endpoint JSON folosit de fetch() pentru dropdown-ul de departamente.
def departamente_pentru_tip(request):
    tip_id = request.GET.get('tip_id', '')
    departamente = []
    if tip_id.isdigit():
        tip = TipMesaj.objects.filter(pk=tip_id).first()
        if tip:
            departamente = list(tip.departamente.order_by('nume').values('id', 'nume'))
    return JsonResponse({'departamente': departamente})


def data_valida(an, luna, zi):
    """Anul e obligatoriu; luna 1-12; ziua 1-31 și numai împreună cu luna."""
    if not an.isdigit():
        return False
    if luna and not (luna.isdigit() and 1 <= int(luna) <= 12):
        return False
    if zi and not (luna and zi.isdigit() and 1 <= int(zi) <= 31):
        return False
    return True


def citeste_mesaje(departament, an, luna, zi):
    """Citește fișierele JSON ale departamentului care se potrivesc cu data cerută."""
    lista = []
    for cale in (MESAJE_DIR / departament.slug).glob('mesaj_*.json'):
        try:
            with open(cale, encoding='utf-8') as fisier:
                date_mesaj = json.load(fisier)
            data_mesaj = datetime.fromisoformat(date_mesaj['data_ora']).date()
        except (ValueError, OSError, KeyError):  # JSONDecodeError este subclasă de ValueError
            continue
        if (data_mesaj.year == int(an)
                and (not luna or data_mesaj.month == int(luna))
                and (not zi or data_mesaj.day == int(zi))):
            date_mesaj['clasa_tip'] = slugify(date_mesaj.get('tip_mesaj', 'mesaj'))
            lista.append(date_mesaj)
    return sorted(lista, key=lambda item: item.get('data_ora', ''), reverse=True)


# Task 3.5–3.6: citim fișiere JSON după departament/an/lună/zi și marcăm urgențele în template.
def mesaje(request):
    departament_slug = request.GET.get('departament', '')
    an = request.GET.get('an', '')
    luna = request.GET.get('luna', '')
    zi = request.GET.get('zi', '')
    lista, eroare = [], ''

    departament = Departament.objects.filter(slug=departament_slug).first() if departament_slug else None
    if departament and data_valida(an, luna, zi):
        lista = citeste_mesaje(departament, an, luna, zi)
    elif request.GET:
        eroare = 'Alege departamentul și anul. Pentru zi trebuie completată și luna.'

    return render(request, 'Atelier_Ciocolata/mesaje.html', {
        'mesaje': lista, 'eroare': eroare, 'departamente': Departament.objects.all(),
        'departament_selectat': departament_slug, 'an': an, 'luna': luna, 'zi': zi,
        'media_url': settings.MEDIA_URL,
    })


# ============================================================
# LABORATORUL 5 – TASK 4: view pentru ModelForm.
# save() face și salvarea relațiilor many-to-many.
# ============================================================
def adauga_prajitura(request):
    if request.method == 'POST':
        formular = AdaugaPrajituraForm(request.POST, request.FILES)
        if formular.is_valid():
            produs = formular.save()
            messages.success(request, f'Produsul „{produs.nume}” a fost adăugat. Preț calculat: {produs.pret} lei.')
            return redirect(produs.get_absolute_url())
        messages.error(request, 'Produsul nu a fost salvat. Verifică erorile din formular.')
    else:
        formular = AdaugaPrajituraForm()
    return render(request, 'Atelier_Ciocolata/adauga_prajitura.html', {'formular': formular})
