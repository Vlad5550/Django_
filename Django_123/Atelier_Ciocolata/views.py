from itertools import count
from urllib.parse import urlsplit
from collections import Counter
 
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

# LAB 2, TASK 1: lista accesărilor păstrată în memoria serverului.
# Se golește automat când serverul Django este repornit.
ACCESARI = []


class Accesare:
    # LAB 1,  4: contor comun pentru ID-uri autoincrementate.
    _contor = count(1)

    # LAB 1,  3 și 7: nume românești pentru zile și luni.
    ZILE = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]
    LUNI = ["Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie", "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]

    # LAB 1,  4: proprietățile fiecărei accesări.
    def __init__(self, ip_client, url, parametri=None):
        self.id = next(self._contor)
        self.ip_client = ip_client
        self.url = url
        self.parametri = parametri if parametri is not None else {}
        self.data = timezone.localtime(timezone.now())

    # LAB 1,  5: listă de tupluri (nume, valoare).
    # Pentru parametrii repetați din URL se păstrează toate valorile.
    def lista_parametri(self):
        rezultat = []
        for nume in self.parametri:
            if isinstance(self.parametri, QueryDict):
                valori = self.parametri.getlist(nume)
                valoare = valori[0] if len(valori) == 1 else valori
            else:
                valoare = self.parametri.get(nume)
            rezultat.append((nume, valoare))
        return rezultat

    # LAB 1,  6: URL complet, inclusiv query string.
    def string_url(self):
        return self.url

    # LAB 1,  6: numai calea paginii, fără domeniu și parametri.
    def pagina(self):
        return urlsplit(self.url).path

    # LAB 1,  3 și 7: formatare cu directive datetime,
    # dar cu numele zilelor și lunilor în limba română.
    def data_text(self, format="%A, %d %B %Y"):
        zile = ["Luni", "Marti", "Miercuri", "Joi", "Vineri", "Sambata", "Duminica"]
        luni = ["Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie","Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]

        data = self.data

        rezultat = format.replace("%A", zile[data.weekday()])
        rezultat = rezultat.replace("%B", luni[data.month - 1])
        rezultat = rezultat.replace("%d", str(data.day))
        rezultat = rezultat.replace("%Y", str(data.year))

        return rezultat

    # LAB 1,  10: parametrul data poate fi "zi" sau "timp".
    # Metoda returnează fragmentul HTML care se inserează în pagina /info.
    def calculeaza_data(self, format="%A, %d %B %Y", data=""):
        titlu = "Data și ora"
        if data == "zi":
            titlu = "Data"
            format = "%d %B %Y"
        elif data == "timp":
            titlu = "Ora"
            format = "%H:%M:%S"
        text = self.data_text(format)
        return f'<section class="panel"><h2>{titlu}</h2><p>{text}</p></section>'

    # LAB 1,  9: afișează ID, IP și rezultatele metodelor clasei.
    def __str__(self):
        return (
            f"id: {self.id}\n"
            f"ip_client: {self.ip_client}\n"
            f"string_url: {self.string_url()}\n"
            f"pagina: {self.pagina()}\n"
            f"calculeaza_data: {self.calculeaza_data()}\n"
            f"lista_parametri: {self.lista_parametri()}"
        )


# LAB 1,  2; LAB 2, TASK 2, 3:
# Pagina principală folosește template-ul care extinde baza.html.
def index(request):
    return render(request, "Atelier_Ciocolata/index.html")


# LAB 1:  2, 3, 7 și 10:
# Pagina /info folosește obiectul Accesare creat de middleware.
def info(request):
    return render(request, "Atelier_Ciocolata/info.html", {
        "data_html": request.accesare.calculeaza_data(data=request.GET.get("data", ""))
    })


# LAB 2, TASK 1,  5;  TASK 2, SUBPUNCTUL 7.
def despre(request):
    return render(request, "Atelier_Ciocolata/despre.html")


def istoric(request):
    return render(request, "Atelier_Ciocolata/istoric.html")


# LAB 2, TASK 2,  10: paginile neimplementate afișează in_lucru.html.
def in_lucru(request, titlu="Pagină"):
    return render(request, "Atelier_Ciocolata/in_lucru.html", {"titlu": titlu})

 
# LAB 2, TASK 1,  4: valorile care pot fi afișate în tabel.
def valoare_camp(accesare, camp):
    campuri = {
        "id": accesare.id,
        "ip_client": accesare.ip_client,
        "url": accesare.string_url(),
        "string_url": accesare.string_url(),
        "pagina": accesare.pagina(),
        "parametri": accesare.lista_parametri(),
        "data": accesare.data_text("%d %B %Y, %H:%M:%S"),
        "calculeaza_data": accesare.data_text("%d %B %Y, %H:%M:%S"),
        "lista_parametri": accesare.lista_parametri(),
    }
    return campuri[camp]


# LAB 2, TASK 1,  1-4:
def log(request):
    # - Afisam toate accesarile
    toate = list(ACCESARI)
    selectate = toate
    mesaje = []

    # - Selectam accesarile dupa ID
    if "iduri" in request.GET:

        iduri = []

        for valoare in request.GET.getlist("iduri"):
            for id in valoare.split(","):
                try:
                    iduri.append(int(id.strip()))
                except ValueError:
                    mesaje.append(f"ID invalid: {id}")

        # Eliminam dublurile daca dubluri nu este true
        if request.GET.get("dubluri", "false") != "true":
            iduri = list(dict.fromkeys(iduri))

        selectate = []

        for id in iduri:
            for a in toate:
                if a.id == id:
                    selectate.append(a)
                    break
            else:
                mesaje.append(f"Nu exista accesarea cu id-ul {id}")

    # - Afisam ultimele n accesari
    elif "ultimele" in request.GET:
        try:
            n = int(request.GET["ultimele"])
            if n < 0:
                raise ValueError
            if n > len(toate):
                mesaje.append(
                    f"Exista doar {len(toate)} accesari fata de {n} accesari cerute"
                )
                selectate = toate
            else:
                selectate = toate[-n:] if n > 0 else []

        except ValueError:
            mesaje.append("Parametrul ultimele trebuie sa fie un numar intreg nenegativ.")
            selectate = []
    # - Parametrul tabel: tot sau o lista de proprietati
    campuri = [ "id", "ip_client", "url", "string_url","pagina", "parametri", "data", "calculeaza_data", "lista_parametri"]

    etichete = {
        "id": "ID",
        "ip_client": "IP client",
        "url": "URL",
        "string_url": "String URL",
        "pagina": "Pagina",
        "parametri": "Parametri",
        "data": "Data",
        "calculeaza_data": "Calculeaza data",
        "lista_parametri": "Lista parametri"
    }

    tabel = request.GET.get("tabel", "")
    coloane = []

    if tabel == "tot":
        coloane = campuri

    elif tabel:
        coloane = tabel.split(",")

        if any(c not in campuri for c in coloane):
            mesaje.append("Campuri invalide pentru tabel")
            coloane = []

    randuri = []

    for a in selectate:
        rand = []
        for c in coloane:
            rand.append(valoare_camp(a, c))
        randuri.append(rand)

    # - Pagina cea mai putin si cea mai mult accesata
    numarari = {}

    for a in toate:
        pagina = a.pagina()
        numarari[pagina] = numarari.get(pagina, 0) + 1

    pagina_minima = min(numarari, key=numarari.get) if numarari else "-"
    pagina_maxima = max(numarari, key=numarari.get) if numarari else "-"

    #  Numarul parametrilor si numele acestora
    nume_parametri = list(request.GET.keys())
    nr_parametri = sum(
        len(request.GET.getlist(p)) for p in nume_parametri
    )
    # - Modurile de afisare: nr si detalii
    accesari = request.GET.get("accesari", "")

    detalii = []

    for a in toate:
        detalii.append((a.id, a.data_text("%d %B %Y, %H:%M:%S")))

    # Trimitem datele catre template
    return render(request, "Atelier_Ciocolata/log.html", {
        "accesari": selectate,
        "total": len(toate),
        "mesaje": mesaje,

        "mod_nr": accesari == "nr",
        "mod_detalii": accesari == "detalii",
        "detalii": detalii,

        "nume_parametri": nume_parametri,
        "nr_parametri": nr_parametri,

        "coloane": [etichete[c] for c in coloane],
        "randuri_tabel": randuri,
        "afiseaza_tabel": bool(tabel and coloane),

        "pagina_minima": pagina_minima,
        "pagina_maxima": pagina_maxima,
    })


# LAB 2, TASK 1,  5: ruta re_path /accesare<ID>.
def accesare_id(request, id):
    id = int(id)  # re_path transmite parametrul capturat ca string.
    for accesare in ACCESARI:
        if accesare.id == id:
            return render(request, "Atelier_Ciocolata/accesare.html", {"accesare": accesare})
    raise Http404("Accesarea nu exista")
