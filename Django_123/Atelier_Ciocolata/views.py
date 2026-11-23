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
    LUNI = ["Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie",
            "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"]

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
            if hasattr(self.parametri, "getlist"):
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
        valori = {
            "%A": self.ZILE[self.data.weekday()],
            "%a": ["Lu", "Ma", "Mi", "Jo", "Vi", "Sâ", "Du"][self.data.weekday()],
            "%B": self.LUNI[self.data.month - 1],
            "%b": ["Ian", "Feb", "Mar", "Apr", "Mai", "Iun", "Iul", "Aug", "Sep", "Oct", "Noi", "Dec"][self.data.month - 1],
            "%d": str(self.data.day),
        }
        marcaje = {}
        for index, (cod, valoare) in enumerate(valori.items()):
            marcaj = f"__DATA_{index}__"
            format = format.replace(cod, marcaj)
            marcaje[marcaj] = valoare
        rezultat = self.data.strftime(format)
        for marcaj, valoare in marcaje.items():
            rezultat = rezultat.replace(marcaj, valoare)
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


# LAB 1,  2; LAB 2, TASK 2, SUBPUNCTUL 3:
# Pagina principală folosește template-ul care extinde baza.html.
def index(request):
    return render(request, "Atelier_Ciocolata/index.html")


# LAB 1:  2, 3, 7 și 10:
# Pagina /info folosește obiectul Accesare creat de middleware.
def info(request):
    return render(request, "Atelier_Ciocolata/info.html", {
        "data_html": request.accesare.calculeaza_data(data=request.GET.get("data", ""))
    })


# LAB 2, TASK 1, SUBPUNCTUL 5; TASK 2, SUBPUNCTUL 7.
def despre(request):
    return render(request, "Atelier_Ciocolata/despre.html")


def istoric(request):
    return render(request, "Atelier_Ciocolata/istoric.html")


# LAB 2, TASK 2, SUBPUNCTUL 10: paginile neimplementate afișează in_lucru.html.
def in_lucru(request, titlu="Pagină"):
    return render(request, "Atelier_Ciocolata/in_lucru.html", {"titlu": titlu})

 
# LAB 2, TASK 1, SUBPUNCTUL 4: valorile care pot fi afișate în tabel.
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


# LAB 2, TASK 1, SUBPUNCTELE 1-4:
# /log listează toate accesările și acceptă filtrele cerute în laborator.
def log(request):
    toate = list(ACCESARI)  # Include și accesarea curentă a paginii /log.
    selectate = toate
    mesaje = []

    # SUBPUNCTUL 2: iduri poate apărea de mai multe ori și conține liste separate prin virgulă.
    if "iduri" in request.GET:
        iduri = []
        for valoare in request.GET.getlist("iduri"):
            for element in valoare.split(","):
                try:
                    iduri.append(int(element.strip()))
                except ValueError:
                    mesaje.append(f"ID invalid: {element}")

        # Fără dubluri implicit; cu dubluri=true se păstrează repetările.
        if request.GET.get("dubluri", "false").lower() != "true":
            iduri = list(dict.fromkeys(iduri))

        dupa_id = {a.id: a for a in toate}
        selectate = []
        for id_accesare in iduri:
            if id_accesare in dupa_id:
                selectate.append(dupa_id[id_accesare])
            else:
                mesaje.append(f"Nu exista accesarea cu id-ul {id_accesare}")

    # SUBPUNCTUL 1: ultimele trebuie să fie număr întreg nenegativ.
    elif "ultimele" in request.GET:
        try:
            n = int(request.GET.get("ultimele", ""))
            if n < 0:
                raise ValueError
            if n > len(toate):
                # Textul este cel cerut în enunț; se afișează la finalul paginii.
                mesaje.append(f"Exista doar {len(toate)} accesari fata de {n} accesari cerute")
                selectate = toate
            else:
                selectate = toate[-n:] if n else []
        except ValueError:
            mesaje.append("Parametrul ultimele trebuie sa fie un numar intreg nenegativ.")
            selectate = []

    # SUBPUNCTUL 4: tabel=tot sau tabel=id,url etc.
    tabel = request.GET.get("tabel", "")
    campuri_disponibile = ["id", "ip_client", "url", "string_url", "pagina", "parametri", "data", "calculeaza_data", "lista_parametri"]
    etichete = {
        "id": "ID", "ip_client": "IP client", "url": "URL", "string_url": "String URL",
        "pagina": "Pagina", "parametri": "Parametri", "data": "Data",
        "calculeaza_data": "Calculeaza data", "lista_parametri": "Lista parametri"
    }
    coloane = []
    if tabel:
        if tabel == "tot":
            coloane = campuri_disponibile
        else:
            coloane = [x.strip() for x in tabel.split(",") if x.strip()]
            invalide = [x for x in coloane if x not in campuri_disponibile]
            if invalide:
                mesaje.append("Campuri invalide pentru tabel: " + ", ".join(invalide))
                coloane = []

    randuri_tabel = [[valoare_camp(a, camp) for camp in coloane] for a in selectate]

    # SUBPUNCTUL 5: pagina cel mai puțin și cel mai mult accesată.
    numarari = Counter(a.pagina() for a in toate)
    pagina_minima = min(numarari, key=numarari.get) if numarari else "-"
    pagina_maxima = max(numarari, key=numarari.get) if numarari else "-"

    # SUBPUNCTUL 3: modurile nr/detalii și lista parametrilor cererii /log.
    nume_parametri = list(request.GET.keys())
    nr_parametri = sum(len(request.GET.getlist(n)) for n in nume_parametri)
    mod_accesari = request.GET.get("accesari", "")

    return render(request, "Atelier_Ciocolata/log.html", {
        "accesari": selectate,
        "total": len(toate),
        "mesaje": mesaje,
        "mod_nr": mod_accesari == "nr",
        "mod_detalii": mod_accesari == "detalii",
        "detalii": [(a.id, a.data_text("%d %B %Y, %H:%M:%S")) for a in toate],
        "nume_parametri": nume_parametri,
        "nr_parametri": nr_parametri,
        "coloane": [etichete[c] for c in coloane],
        "randuri_tabel": randuri_tabel,
        "afiseaza_tabel": bool(tabel and coloane),
        "pagina_minima": pagina_minima,
        "pagina_maxima": pagina_maxima,
    })


# LAB 2, TASK 1, SUBPUNCTUL 5: ruta re_path /accesare<ID>.
def accesare_id(request, id):
    id = int(id)  # re_path transmite parametrul capturat ca string.
    for accesare in ACCESARI:
        if accesare.id == id:
            return render(request, "Atelier_Ciocolata/accesare.html", {"accesare": accesare})
    raise Http404("Accesarea nu exista")
