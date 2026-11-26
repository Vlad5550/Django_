
from itertools import count
from urllib.parse import urlsplit

from django.http import Http404, QueryDict
from django.shortcuts import render
from django.utils import timezone


# LAB 2, TASK 1:
# Lista globală păstrează accesările în memoria serverului.
# Se golește la repornirea serverului.
ACCESARI = []


class Accesare:

    # LAB 1,  4:
    # Contor comun pentru ID-uri autoincrementate.
    _contor = count(1)

    # LAB 1,   3 și 7:
    # Numele zilelor și lunilor în limba română.
    ZILE = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]
    LUNI = ["Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie",
            "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]

    # LAB 1,  4:
    # Constructorul inițializează obiectul și atributele sale.
    def __init__(self, ip_client, url, parametri=None):
        self.id = next(self._contor)
        self.ip_client = ip_client
        self.url = url
        self.parametri = parametri if parametri is not None else {}
        self.data = timezone.localtime(timezone.now())

    # LAB 1,  5:
    # Returnează parametrii ca listă de tupluri (nume, valoare).
    # QueryDict și getlist() permit păstrarea valorilor parametrilor repetați.
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

    # LAB 1,  6:
    # Returnează URL-ul complet sau doar calea paginii.
    def string_url(self):
        return self.url

    def pagina(self):
        return urlsplit(self.url).path

    # LAB 1, SUBPUNCTELE 3 și 7:
    # Formatează data folosind numele românești ale zilelor și lunilor.
    def data_text(self, format="%A, %d %B %Y"):
        data = self.data

        inlocuiri = {
            "%A": self.ZILE[data.weekday()],
            "%B": self.LUNI[data.month - 1],
            "%d": f"{data.day:02d}",
            "%Y": str(data.year),
            "%H": f"{data.hour:02d}",
            "%M": f"{data.minute:02d}",
            "%S": f"{data.second:02d}",
        }

        rezultat = format
        for directiva, valoare in inlocuiri.items():
            rezultat = rezultat.replace(directiva, valoare)

        return rezultat

    # LAB 1,  10:
    # Parametrul data decide dacă se afișează data, ora sau ambele.
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

    # LAB 1,  9:
    # __str__ definește reprezentarea textuală a obiectului.
    def __str__(self):
        return (
            f"id: {self.id}\n"
            f"ip_client: {self.ip_client}\n"
            f"string_url: {self.string_url()}\n"
            f"pagina: {self.pagina()}\n"
            f"calculeaza_data: {self.calculeaza_data()}\n"
            f"lista_parametri: {self.lista_parametri()}"
        )



# LAB 1 și LAB 2, TASK 2:
# FUNCȚII VIEW PENTRU PAGINI
def index(request):
    return render(request, "Atelier_Ciocolata/index.html")


# LAB 1, SUBPUNCTELE 2, 3, 7 și 10:
# Folosește obiectul creat de middleware și parametrul GET "data".
def info(request):
    return render(request, "Atelier_Ciocolata/info.html", {
        "data_html": request.accesare.calculeaza_data(
            data=request.GET.get("data", "")
        )
    })


# LAB 2, TASK 1,  5; TASK 2,  7.
def despre(request):
    return render(request, "Atelier_Ciocolata/despre.html")


def istoric(request):
    return render(request, "Atelier_Ciocolata/istoric.html")


# LAB 2, TASK 2,  10:
# Pagină generică pentru funcționalitățile neimplementate.
def in_lucru(request, titlu="Pagină"):
    return render(request, "Atelier_Ciocolata/in_lucru.html", {"titlu": titlu})


# LAB 2, TASK 1,  4:
# SELECTAREA VALORII UNUI CÂMP PENTRU TABEL

# Dicționarul permite asocierea numelui unui câmp cu valoarea sa.
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


# LAB 2, TASK 1, SUBPUNCTELE 1-5:
# FUNCȚIA PRINCIPALĂ A JURNALULUI
def log(request):

    #  1: implicit, sunt selectate toate accesările.
    toate = list(ACCESARI)
    selectate = toate
    mesaje = []

    #  2: selectarea după ID-uri primite prin URL.
    # getlist() acceptă parametri repetați, iar split() separă ID-urile prin virgulă.
    if "iduri" in request.GET:

        iduri = []

        for valoare in request.GET.getlist("iduri"):
            for id in valoare.split(","):
                try:
                    iduri.append(int(id.strip()))
                except ValueError:
                    mesaje.append(f"ID invalid: {id}")

        # dict.fromkeys() elimină duplicatele și păstrează ordinea,
        # exceptând situația în care dubluri=true.
        if request.GET.get("dubluri", "false") != "true":
            iduri = list(dict.fromkeys(iduri))

        selectate = []
        # Caută fiecare ID în lista accesărilor.
        # for-else execută else dacă nu s-a întâlnit break.
        for id in iduri:
            for a in toate:
                if a.id == id:
                    selectate.append(a)
                    break
            else:
                mesaje.append(f"Nu exista accesarea cu id-ul {id}")

    #  3: selectarea ultimelor N accesări.
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
                # Slicing-ul [-n:] selectează ultimele N elemente.
                # Pentru n=0 folosim [] deoarece [-0:] ar returna toată lista.
                selectate = toate[-n:] if n > 0 else []

        except ValueError:
            mesaje.append(
                "Parametrul ultimele trebuie sa fie un numar intreg nenegativ."
            )
            selectate = []

    #  4: câmpurile permise pentru afișarea în tabel.
    campuri = [
        "id", "ip_client", "url", "string_url", "pagina",
        "parametri", "data", "calculeaza_data", "lista_parametri"
    ]

    # Dicționar pentru transformarea numelor tehnice în etichete lizibile.
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

    # Citește coloanele solicitate prin parametrul GET "tabel".
    tabel = request.GET.get("tabel", "")
    coloane = []

    if tabel == "tot":
        coloane = campuri

    elif tabel:
        coloane = tabel.split(",")

        # any() verifică dacă există cel puțin un câmp invalid.
        if any(c not in campuri for c in coloane):
            mesaje.append("Campuri invalide pentru tabel")
            coloane = []

    # Construiește rândurile tabelului folosind valorile câmpurilor selectate.
    randuri = []

    for a in selectate:
        rand = []
        for c in coloane:
            rand.append(valoare_camp(a, c))
        randuri.append(rand)

    #  5: statistici privind paginile accesate.       Dicționarul numarari memorează pagina și numărul ei de accesări.
    numarari = {}

    for a in toate:
        pagina = a.pagina()
        numarari[pagina] = numarari.get(pagina, 0) + 1

    # min() și max() identifică paginile   cu cele mai puține,  respectiv cele mai multe accesări.
    pagina_minima = min(numarari, key=numarari.get) if numarari else "-"
    pagina_maxima = max(numarari, key=numarari.get) if numarari else "-"

    # Numără valorile parametrilor GET și reține numele acestora.
    nume_parametri = list(request.GET.keys())
    nr_parametri = sum(len(request.GET.getlist(p)) for p in nume_parametri)

    # Modurile de afișare: "nr" sau "detalii".
    accesari = request.GET.get("accesari", "")
    detalii = []

    for a in toate:
        detalii.append((a.id, a.data_text("%d %B %Y, %H:%M:%S")))

    # Transmite datele calculate către template-ul log.html.
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

# LAB 2, TASK 1,  5:
# re_path transmite ID-ul capturat ca string.
# Căutăm accesarea și afișăm pagina individuală.
def accesare_id(request, id):
    id = int(id)

    for accesare in ACCESARI:
        if accesare.id == id:
            return render(
                request,
                "Atelier_Ciocolata/accesare.html",
                {"accesare": accesare}
            )

    # Dacă ID-ul nu există, returnează eroarea HTTP 404.
    raise Http404("Accesarea nu exista")
