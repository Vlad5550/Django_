from collections import Counter
from datetime import datetime
from urllib.parse import urlsplit
from django.http import Http404
from django.shortcuts import render


DESCRIERE = (
    'Atelierul de ciocolată este un magazin de prăjituri și produse de '
    'cofetărie pe bază de ciocolată.'
)
ZILE = ('Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică')
LUNI = (
    'Ianuarie', 'Februarie', 'Martie', 'Aprilie', 'Mai', 'Iunie',
    'Iulie', 'August', 'Septembrie', 'Octombrie', 'Noiembrie', 'Decembrie'
)
FORMAT_DATA = '%A, %-d %B %Y'

   
# LAB 1 -   4-7: datele unei accesări și metodele cerute.
class Accesare:
    urmatorul_id = 1

    def __init__(self, ip_client, url, parametri=None, data=None):
        self.id = Accesare.urmatorul_id
        Accesare.urmatorul_id += 1
        self.ip_client = ip_client
        self.url = url
        self.parametri = {} if parametri is None else parametri
        self.data = datetime.now() if data is None else data

    # LAB 1 -   5: listă de tupluri (nume, valoare).
    def lista_parametri(self):
        """Returnează perechi (nume, valoare); valorile goale devin None."""
        rezultat = []
        for nume, valoare in self.parametri.items():
            if isinstance(valoare, list):
                valoare = [v if v != '' else None for v in valoare]
            elif valoare == '':
                valoare = None
            rezultat.append((nume, valoare))
        return rezultat

    # LAB 1 -   6: URL complet, inclusiv query string.
    def string_url(self):
        return self.url

    # LAB 1 -   6: doar calea paginii, fără domeniu sau parametri.
    def pagina(self):
        return urlsplit(self.url).path

    # LAB 1 - 7 și 10: data în română; tipul poate fi zi sau timp.
    def calculeaza_data(self, format=FORMAT_DATA, tip=''):
        """Formatează data în română și returnează secțiunea HTML."""
        adauga_ora = tip == '' and format == FORMAT_DATA
        if tip == 'zi':
            format = '%-d %B %Y'
        elif tip == 'timp':
            format = '%H:%M:%S'

        # Înlocuim codurile românești înainte de strftime (compatibil Windows).
        format = (format.replace('%A', ZILE[self.data.weekday()])
                        .replace('%a', ZILE[self.data.weekday()][:3])
                        .replace('%B', LUNI[self.data.month - 1])
                        .replace('%b', LUNI[self.data.month - 1][:3])
                        .replace('%-d', str(self.data.day)))
        valoare = self.data.strftime(format)
        if adauga_ora:
            valoare += ' ' + self.data.strftime('%H:%M:%S')
        return f'<section><h2>Data și ora</h2><p>{valoare}</p></section>'

    # LAB 1 -   9: rezumatul accesării, afișat de middleware în consolă.
    def __str__(self):                                                                # 
        return (
            f'id: {self.id}\n'
            f'ip_client: {self.ip_client}\n'
            f'string_url: {self.string_url()}\n'
            f'pagina: {self.pagina()}\n'
            f'calculeaza_data: {self.calculeaza_data()}\n'
            f'lista_parametri: {self.lista_parametri()}'
        )


# Lista păstrează accesările în memoria serverului (sesiunea curentă).
accesari = []

def index(request):
    return render(request, 'Atelier_Ciocolata/index.html', {'descriere': DESCRIERE})

# LAB 1 -  2, 3 și 10: pagina info și parametrul ?data=zi/timp.
def info(request):
    # ?data=zi afișează doar data, iar ?data=timp afișează doar ora.
    sectiune = request.accesare.calculeaza_data(tip=request.GET.get('data', ''))
    return render(request, 'Atelier_Ciocolata/info.html', {'sectiune': sectiune})

def despre(request):
    return render(request, 'Atelier_Ciocolata/despre.html')

def istoric(request):
    return render(request, 'Atelier_Ciocolata/istoric.html')

def in_lucru(request):
    return render(request, 'Atelier_Ciocolata/in_lucru.html')


# LAB 2 -   1-4: listă, filtre, statistici și tabelul accesărilor.
def log(request):
    # Implicit afișăm toate accesările, inclusiv cererea curentă către /log.
    selectie = list(accesari)
    eroare = ''

    # iduri poate apărea de mai multe ori; ordinea cerută este păstrată.
    if 'iduri' in request.GET:
        dupa_id = {a.id: a for a in accesari}
        dubluri = request.GET.get('dubluri', 'false').lower() == 'true'
        selectie, folosite = [], set()
        for valoare in request.GET.getlist('iduri'):
            for text_id in valoare.split(','):
                text_id = text_id.strip()
                if text_id.isascii() and text_id.isdecimal():
                    id_accesare = int(text_id)
                    if id_accesare in dupa_id and (dubluri or id_accesare not in folosite):
                        selectie.append(dupa_id[id_accesare])
                        folosite.add(id_accesare)

    # ultimele trebuie să fie un număr întreg nenegativ.
    if 'ultimele' in request.GET:
        valoare = request.GET['ultimele']
        if not valoare.isascii() or not valoare.isdecimal():
            eroare = 'Parametrul ultimele trebuie să fie un număr întreg nenegativ.'
            selectie = []
        else:
            n = int(valoare)
            if n > len(selectie):
                eroare = f'Exista doar {len(selectie)} accesari fata de {n} accesari cerute'
            selectie = selectie[-n:] if n else []

    # Opțiunile accesari=nr și accesari=detalii.
    optiune = request.GET.get('accesari')
    numar_accesari = len(accesari) if optiune == 'nr' else None
    detalii = selectie if optiune == 'detalii' else None

    # Tabelul poate conține toate câmpurile sau doar câmpurile cerute.
    toate_coloanele = ('id', 'ip_client', 'url', 'parametri', 'data')
    tabel = request.GET.get('tabel')
    coloane = []
    randuri = []
    if tabel is not None:
        coloane = list(toate_coloanele) if tabel == 'tot' else [
            camp for camp in tabel.split(',') if camp in toate_coloanele
        ]
        randuri = [
            [str(getattr(a, camp)) for camp in coloane]
            for a in selectie
        ]

    frecventa = Counter(a.pagina() for a in accesari)
    # Repetăm numele când un parametru a fost transmis de mai multe ori.
    parametri = [nume for nume, valori in request.GET.lists() for _ in valori]

    return render(request, 'Atelier_Ciocolata/log.html', {
        'accesari': selectie,
        'eroare': eroare,
        'numar_accesari': numar_accesari,
        'detalii': detalii,
        'coloane': coloane,
        'randuri': randuri,
        'tabel': tabel is not None,
        'numar_parametri': len(parametri),
        'parametri': parametri,
        'pagina_minima': min(frecventa, key=frecventa.get) if frecventa else None,
        'pagina_maxima': max(frecventa, key=frecventa.get) if frecventa else None,
    })


# LAB 2 -   5: afișează accesarea identificată prin ID.
def detalii_accesare(request, id):
    accesare = next((a for a in accesari if a.id == int(id)), None)
    if accesare is None:
        raise Http404('Accesarea nu există.')
    return render(request, 'Atelier_Ciocolata/accesare.html', {'accesare': accesare})


# Opțional: afișează valorile parametrilor primiți în query string.
def afiseaza_liste(request):
    parametri = [
        {'nume': nume, 'valori': request.GET.getlist(nume)}
        for nume in request.GET
    ]
    return render(request, 'Atelier_Ciocolata/liste.html', {'parametri': parametri})


# Opțional: calculează și afișează câteva operații aritmetice.
def operatii(request):
    lista = [                                                                 #defineste datele
        {'a': 10, 'b': 20, 'operatie': 'suma'},
        {'a': 40, 'b': 20, 'operatie': 'diferenta'},
        {'a': 25, 'b': 30, 'operatie': 'suma'},
        {'a': 40, 'b': 30, 'operatie': 'diferenta'},
        {'a': 100, 'b': 50, 'operatie': 'diferenta'},
    ]
    for element in lista:                                                     #prelucreaza datele
        if element['operatie'] == 'suma':
            element['semn'] = '+'
            element['rezultat'] = element['a'] + element['b']
        else:
            element['semn'] = '-'
            element['rezultat'] = element['a'] - element['b']
    return render(request, 'Atelier_Ciocolata/operatii.html', {'lista': lista})     #afiseaza pagina cu datele
