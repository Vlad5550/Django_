import re
from datetime import date
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Prajitura, Categorie, Ambalaj, TipMesaj, Departament
from .utils import varsta_ani_luni


# ============================================================
# VALIDATOARE REUTILIZABILE
# Sunt folosite mai jos la ContactForm și AdaugaPrajituraForm.
# ============================================================
def validare_litera_mare(valoare):
    if valoare and not re.fullmatch(r'[A-ZĂÂÎȘȚ][A-Za-zĂÂÎȘȚăâîșț -]*', valoare):
        raise ValidationError('Textul trebuie să înceapă cu literă mare și să conțină doar litere, spații sau cratime.')


def validare_majuscule_dupa_separator(valoare):
    if valoare and not re.fullmatch(r'[A-ZĂÂÎȘȚ][a-zăâîșțA-ZĂÂÎȘȚ]*(?:[ -][A-ZĂÂÎȘȚ][a-zăâîșțA-ZĂÂÎȘȚ]*)*', valoare):
        raise ValidationError('După fiecare spațiu sau cratimă trebuie să urmeze o literă mare.')



def validare_nume_produs(valoare):
    if valoare and not re.fullmatch(r'[A-ZĂÂÎȘȚ0-9][A-Za-z0-9ĂÂÎȘȚăâîșț -]*', valoare):
        raise ValidationError('Numele produsului trebuie să înceapă cu literă mare și să conțină doar litere, cifre, spații sau cratime.')


def validare_fara_linkuri(valoare):
    if re.search(r'https?://|\b(?:[A-Za-z0-9-]+\.){2,}[A-Za-z]{2,}\b', valoare or '', re.I):
        raise ValidationError('Linkurile și adresele de tip domeniu nu sunt permise.')


# ============================================================
# LABORATORUL 5 – TASK 2: FORMULARUL DE FILTRARE A PRODUSELOR
# 2.1: formularul extinde forms.Form și are câmpuri pentru produsele
#      din modelul Prajitura (inclusiv filtre pentru relații).
# 2.4: widget-urile sunt potrivite tipului de date (număr, dată, select).
# ============================================================
class FiltruProduseForm(forms.Form):
    # 2.1 – câmpuri text și numerice; prețul are minim și maxim separat.
    id = forms.IntegerField(required=False, min_value=1, label='ID produs')
    nume = forms.CharField(required=False, label='Nume', widget=forms.TextInput(attrs={'placeholder': 'Numele produsului'}))
    descriere = forms.CharField(required=False, label='Descriere', widget=forms.TextInput())
    pret_min = forms.DecimalField(required=False, min_value=0, label='Preț minim', widget=forms.NumberInput(attrs={'step': '0.01'}))
    pret_max = forms.DecimalField(required=False, min_value=0, label='Preț maxim', widget=forms.NumberInput(attrs={'step': '0.01'}))
    gramaj_min = forms.IntegerField(required=False, min_value=0, label='Gramaj minim')
    gramaj_max = forms.IntegerField(required=False, min_value=0, label='Gramaj maxim')
    calorii_min = forms.IntegerField(required=False, min_value=0, label='Calorii minime')
    calorii_max = forms.IntegerField(required=False, min_value=0, label='Calorii maxime')
    stoc_min = forms.IntegerField(required=False, min_value=0, label='Stoc minim')
    stoc_max = forms.IntegerField(required=False, min_value=0, label='Stoc maxim')
    stoc_rezervat_min = forms.IntegerField(required=False, min_value=0, label='Stoc rezervat minim')
    stoc_rezervat_max = forms.IntegerField(required=False, min_value=0, label='Stoc rezervat maxim')
    # 2.1 și 2.6 – select pentru tip produs și ForeignKey către Categorie.
    tip_produs = forms.ChoiceField(required=False, label='Tip produs', choices=[('', 'Toate')] + list(Prajitura.TipProdus.choices))
    categorie = forms.ModelChoiceField(required=False, label='Categorie', queryset=Categorie.objects.all())
    pt_diabetici = forms.ChoiceField(required=False, label='Pentru diabetici', choices=[('', 'Toate'), ('da', 'Da'), ('nu', 'Nu')])
    imagine = forms.ChoiceField(required=False, label='Imagine', choices=[('', 'Toate'), ('da', 'Cu imagine'), ('nu', 'Fără imagine')])
    # 2.1 – filtre pentru imagine, ingrediente și taguri.
    ingredient = forms.CharField(required=False, label='Ingredient', help_text='Caută un ingredient.')
    tag_cautat = forms.CharField(required=False, label='Tag / cuvânt cheie')
    ambalaj = forms.ModelChoiceField(required=False, label='Ambalaj', queryset=Ambalaj.objects.all())
    data_de_la = forms.DateField(required=False, label='Creat de la', widget=forms.DateInput(attrs={'type': 'date'}))
    data_pana_la = forms.DateField(required=False, label='Creat până la', widget=forms.DateInput(attrs={'type': 'date'}))
    # 2.7 și 2.8 – utilizatorul alege numărul de produse și coloanele gridului.
    # Valorile 6, 12, 18, 24 se împart exact la 1, 2 sau 3 coloane.
    coloane = forms.ChoiceField(required=False, label='Coloane', choices=[('1', '1 coloană'), ('2', '2 coloane'), ('3', '3 coloane')], initial='3')
    per_page = forms.ChoiceField(required=False, label='Produse pe pagină', choices=[('6', '6'), ('12', '12'), ('18', '18'), ('24', '24')], initial='6')

    # 2.9 – în pagina categoriei câmpul categorie este ascuns și blocat vizual.
    # clean_categorie() verifică din nou valoarea pe server.
    def __init__(self, *args, categorie_fixa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.categorie_fixa = categorie_fixa
        if categorie_fixa:
            self.fields['categorie'].widget = forms.HiddenInput(attrs={'readonly': 'readonly'})
            self.initial['categorie'] = categorie_fixa.pk

    # 2.5 – validări individuale: intervalul de preț trebuie să fie corect.
    def clean_pret_max(self):
        valoare = self.cleaned_data.get('pret_max')
        minim = self.cleaned_data.get('pret_min')
        if valoare is not None and minim is not None and minim > valoare:
            raise ValidationError('Prețul minim nu poate fi mai mare decât prețul maxim.')
        return valoare

    # 2.5 – stocul minim nu poate fi mai mare decât stocul maxim.
    def clean_stoc_max(self):
        valoare = self.cleaned_data.get('stoc_max')
        minim = self.cleaned_data.get('stoc_min')
        if valoare is not None and minim is not None and minim > valoare:
            raise ValidationError('Stocul minim nu poate depăși stocul maxim.')
        return valoare

    # 2.5 – data de început trebuie să fie înaintea datei de final.
    def clean_data_pana_la(self):
        valoare = self.cleaned_data.get('data_pana_la')
        minim = self.cleaned_data.get('data_de_la')
        if valoare and minim and minim > valoare:
            raise ValidationError('Data de început trebuie să fie înaintea datei de final.')
        return valoare

    # 2.9 – protecție server-side împotriva modificării categoriei ascunse.
    def clean_categorie(self):
        categorie = self.cleaned_data.get('categorie')
        if self.categorie_fixa and categorie != self.categorie_fixa:
            raise ValidationError('Nu poți schimba categoria în pagina acestei categorii.')
        return categorie


# ============================================================
# LABORATORUL 5 – TASK 3: FORMULARUL DE CONTACT (forms.Form)
# 3.1: câmpurile formularului; 3.2: validări pe câmpuri;
# 3.3: validări comune în clean(); imaginile sunt opționale.
# ============================================================
class ContactForm(forms.Form):
    # 3.1.1 – nume obligatoriu (max. 10) și prenume opțional (max. 30).
    nume = forms.CharField(max_length=10, label='Nume', error_messages={'required': 'Numele este obligatoriu.', 'max_length': 'Numele poate avea maximum 10 caractere.'}, validators=[validare_litera_mare, validare_majuscule_dupa_separator])
    prenume = forms.CharField(max_length=30, required=False, label='Prenume', error_messages={'max_length': 'Prenumele poate avea maximum 30 de caractere.'}, help_text='Prenumele pot fi separate prin spațiu sau linioară.', validators=[validare_litera_mare, validare_majuscule_dupa_separator])
    # 3.1.2 și 3.2.4 – CNP opțional, exact 13 cifre; verificarea este în clean_cnp().
    cnp = forms.CharField(max_length=13, min_length=13, required=False, label='CNP', error_messages={'min_length': 'CNP-ul trebuie să aibă exact 13 cifre.', 'max_length': 'CNP-ul trebuie să aibă exact 13 cifre.'}, widget=forms.TextInput(attrs={'maxlength': 13, 'id': 'id_cnp'}))
    # 3.1.3–3.1.5 – calendar, e-mail cu confirmare și telefon opțional.
    data_nasterii = forms.DateField(label='Data nașterii', error_messages={'required': 'Data nașterii este obligatorie.', 'invalid': 'Introdu o dată validă.'}, widget=forms.DateInput(attrs={'type': 'date'}))
    email = forms.EmailField(label='E-mail', error_messages={'required': 'Adresa de e-mail este obligatorie.', 'invalid': 'Introdu o adresă de e-mail validă.'})
    confirmare_email = forms.EmailField(label='Confirmare e-mail', error_messages={'required': 'Confirmarea e-mailului este obligatorie.', 'invalid': 'Introdu o adresă de e-mail validă.'})
    telefon = forms.CharField(max_length=20, required=False, label='Telefon', help_text='Exemplu: 0712345678 sau +40712345678.')
    # 3.1.6–3.1.7 – tipul și departamentul sunt preluate din baza de date.
    tip_mesaj = forms.ModelChoiceField(queryset=TipMesaj.objects.all(), empty_label='neselectat', label='Tip mesaj', error_messages={'required': 'Alege un tip de mesaj.', 'invalid_choice': 'Tipul de mesaj selectat nu este valid.'})
    departament = forms.ModelChoiceField(queryset=Departament.objects.all(), empty_label='neselectat', label='Departament destinație', error_messages={'required': 'Alege un departament.', 'invalid_choice': 'Departamentul selectat nu este valid.'})
    # 3.1.8–3.1.10 – subiect, zile de așteptare și mesajul utilizatorului.
    subiect = forms.CharField(max_length=100, label='Subiect', error_messages={'required': 'Subiectul este obligatoriu.', 'max_length': 'Subiectul poate avea maximum 100 de caractere.'}, validators=[validare_litera_mare, validare_fara_linkuri])
    minim_zile = forms.IntegerField(min_value=1, max_value=30, label='Minim zile așteptare', error_messages={'required': 'Completează numărul de zile.', 'min_value': 'Numărul minim este 1 zi.', 'max_value': 'Poți aștepta cel mult 30 de zile.', 'invalid': 'Introdu un număr întreg de zile.'}, help_text='Pentru review-uri/cereri minimul este 4 zile; pentru reclamații/întrebări/programări minimul este 2 zile. Maximul este 30.')
    mesaj = forms.CharField(label='Mesaj (semnați cu numele la final)', error_messages={'required': 'Mesajul este obligatoriu.'}, widget=forms.Textarea(attrs={'rows': 6}), validators=[validare_fara_linkuri])
    # 3.1.11 – maximum trei imagini opționale. Afișarea treptată se face în contact.html.
    imagine1 = forms.ImageField(required=False, label='Imagine 1', error_messages={'invalid_image': 'Fișierul nu este o imagine validă.'})
    imagine2 = forms.ImageField(required=False, label='Imagine 2', error_messages={'invalid_image': 'Fișierul nu este o imagine validă.'})
    imagine3 = forms.ImageField(required=False, label='Imagine 3', error_messages={'invalid_image': 'Fișierul nu este o imagine validă.'})
    # 3.1.12–3.1.13 – acord GDPR și cod ascuns generat de server.
    gdpr = forms.BooleanField(required=True, initial=False, error_messages={'required': 'Acordul GDPR este obligatoriu.'}, label='Sunt de acord cu prelucrarea datelor personale (GDPR).')
    cod_cerere = forms.CharField(widget=forms.HiddenInput(), error_messages={'required': 'Codul cererii lipsește. Reîncarcă formularul.'})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields['departament'].queryset = Departament.objects.none()

    # 3.2.4 – verifică cifrele, prima cifră și data înscrisă în CNP.
    def clean_cnp(self):
        cnp = self.cleaned_data.get('cnp', '')
        if not cnp:
            return cnp
        if not cnp.isdigit() or cnp[0] not in '1256':
            raise ValidationError('CNP-ul trebuie să conțină 13 cifre și să înceapă cu 1, 2, 5 sau 6.')
        an = int(cnp[1:3]) + (2000 if cnp[0] in '56' else 1900)
        luna = int(cnp[3:5])
        zi = int(cnp[5:7])
        try:
            date(an, luna, zi)
        except ValueError:
            raise ValidationError('Data inclusă în CNP nu este validă.')
        return cnp

    # 3.2.1 – persoana trebuie să fie majoră; funcția de vârstă este reutilizată.
    def clean_data_nasterii(self):
        data = self.cleaned_data['data_nasterii']
        azi = timezone.localdate()
        if data > azi:
            raise ValidationError('Data nașterii nu poate fi în viitor.')
        ani, luni = varsta_ani_luni(data)
        if ani < 18:
            raise ValidationError('Trebuie să aveți cel puțin 18 ani pentru a trimite mesajul.')
        return data

    def clean_confirmare_email(self):
        return self.cleaned_data['confirmare_email'].lower()

    # 3.2.5 – respinge domeniile de e-mail temporar.
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        domeniu = email.rsplit('@', 1)[-1]
        if domeniu in ('guerillamail.com', 'yopmail.com'):
            raise ValidationError('Adresele de e-mail temporare nu sunt acceptate.')
        return email

    # 3.2.2 – verifică numărul de cuvinte și lungimea fiecărui cuvânt.
    def clean_mesaj(self):
        text = self.cleaned_data['mesaj'].strip()
        cuvinte = re.findall(r'[A-Za-z0-9ĂÂÎȘȚăâîșț]+', text)
        if not 5 <= len(cuvinte) <= 100:
            raise ValidationError('Mesajul trebuie să conțină între 5 și 100 de cuvinte.')
        if any(len(cuvant) > 15 for cuvant in cuvinte):
            raise ValidationError('Fiecare cuvânt din mesaj trebuie să aibă cel mult 15 caractere.')
        return text

    # 3.2.8 – verifică acordul și pe server, nu doar prin butonul HTML.
    def clean_gdpr(self):
        if self.cleaned_data.get('gdpr') is not True:
            raise ValidationError('Acordul GDPR este obligatoriu.')
        return True

    # 3.2.9 – verifică formatul codului generat de aplicație.
    def clean_cod_cerere(self):
        cod = self.cleaned_data['cod_cerere']
        if not re.fullmatch(r'[A-Z]{3}[a-z]{2}[0-9]{8}', cod):
            raise ValidationError('Codul cererii nu este valid. Reîncărcați formularul.')
        return cod

    # 3.3 – validări între câmpuri: e-mail, semnătură, zile, CNP și departament.
    def clean(self):
        date_curate = super().clean()
        email = date_curate.get('email')
        confirmare = date_curate.get('confirmare_email')
        if email and confirmare and email != confirmare:
            self.add_error('confirmare_email', 'Cele două adrese de e-mail trebuie să coincidă.')

        nume = date_curate.get('nume')
        mesaj = date_curate.get('mesaj')
        # Extragem ultimul cuvânt, ignorând semnele de punctuație de la final.
        ultimele_cuvinte = re.findall(r'[A-Za-zĂÂÎȘȚăâîșț]+', mesaj or '')
        if nume and ultimele_cuvinte and ultimele_cuvinte[-1].casefold() != nume.casefold():
            self.add_error('mesaj', 'Ultimul cuvânt din mesaj trebuie să fie numele dumneavoastră (semnătura).')

        tip = date_curate.get('tip_mesaj')
        departament = date_curate.get('departament')
        zile = date_curate.get('minim_zile')
        if tip and zile is not None and zile < tip.minim_zile:
            self.add_error('minim_zile', f'Pentru tipul {tip.nume}, trebuie să așteptați minimum {tip.minim_zile} zile.')
        if tip and departament and not tip.departamente.filter(pk=departament.pk).exists():
            self.add_error('departament', 'Departamentul selectat nu poate primi acest tip de mesaj.')

        cnp = date_curate.get('cnp')
        nastere = date_curate.get('data_nasterii')
        if cnp and nastere:
            an = int(cnp[1:3]) + (2000 if cnp[0] in '56' else 1900)
            try:
                data_cnp = date(an, int(cnp[3:5]), int(cnp[5:7]))
                if data_cnp != nastere:
                    self.add_error('cnp', 'Data din CNP nu coincide cu data nașterii.')
            except ValueError:
                self.add_error('cnp', 'Data din CNP nu este validă.')
        return date_curate
 

# ============================================================
# LABORATORUL 5 – TASK 4: FORMULAR ModelForm PENTRU PRODUS
# 4.1–4.2: formular legat de modelul Prajitura, cu unele câmpuri din model.
# 4.3: cost_preparare și adaos_procent sunt inputuri suplimentare.
# ============================================================
class AdaugaPrajituraForm(forms.ModelForm):
    # Două câmpuri suplimentare, care nu există în tabelul Prajitura.
    cost_preparare = forms.DecimalField(label='Cost preparare (lei)', min_value=Decimal('0.01'), error_messages={'required': 'Completează costul preparării.', 'min_value': 'Costul trebuie să fie mai mare decât zero.', 'invalid': 'Introdu un cost numeric valid.'}, help_text='Input suplimentar pentru calcularea prețului.')
    adaos_procent = forms.DecimalField(label='Adaos (%)', min_value=Decimal('1'), max_value=Decimal('200'), error_messages={'required': 'Completează adaosul procentual.', 'min_value': 'Adaosul minim este 1%.', 'max_value': 'Adaosul maxim este 200%.', 'invalid': 'Introdu un procent valid.'}, help_text='Input suplimentar; prețul se calculează automat.')
    nume = forms.CharField(max_length=50, label='Numele produsului', validators=[validare_nume_produs, validare_fara_linkuri], help_text='Începeți cu literă mare.')
    descriere = forms.CharField(required=False, label='Descrierea produsului', widget=forms.Textarea(attrs={'rows': 3}), validators=[validare_fara_linkuri], help_text='Nu introduceți linkuri.')
    gramaj = forms.IntegerField(label='Gramaj (grame)', min_value=10, error_messages={'required': 'Completează gramajul.', 'min_value': 'Gramajul minim este 10 grame.', 'invalid': 'Gramajul trebuie să fie un număr întreg.'})
    calorii = forms.IntegerField(label='Calorii / porție', min_value=0, error_messages={'required': 'Completează numărul de calorii.', 'min_value': 'Caloriile nu pot fi negative.', 'invalid': 'Introdu un număr întreg de calorii.'})
    stoc = forms.IntegerField(label='Stoc disponibil', min_value=0, error_messages={'required': 'Completează stocul.', 'min_value': 'Stocul nu poate fi negativ.', 'invalid': 'Stocul trebuie să fie un număr întreg.'})

    # 4.1–4.2 – Meta stabilește modelul și câmpurile care apar în formular.
    class Meta:
        model = Prajitura
        fields = ['nume', 'descriere', 'gramaj', 'calorii', 'stoc', 'tip_produs', 'categorie', 'pt_diabetici', 'ingrediente', 'taguri']
        labels = {
            'gramaj': 'Gramaj (grame)',
            'calorii': 'Calorii / porție',
            'stoc': 'Stoc disponibil',
            'categorie': 'Categoria produsului',
        }
        help_texts = {
            'gramaj': 'Gramajul unei porții.',
            'taguri': 'Cuvinte cheie separate prin virgulă.',
        }

    # 4.5 – validări individuale pentru gramaj, calorii și stoc.
    def clean_gramaj(self):
        valoare = self.cleaned_data['gramaj']
        if valoare < 10:
            raise ValidationError('Gramajul trebuie să fie de minimum 10 grame.')
        return valoare

    def clean_calorii(self):
        valoare = self.cleaned_data['calorii']
        if valoare > 1500:
            raise ValidationError('Caloriile pe porție nu pot depăși 1500.')
        return valoare

    def clean_stoc(self):
        valoare = self.cleaned_data['stoc']
        if valoare > 50000:
            raise ValidationError('Stocul este prea mare; limita este 50000.')
        return valoare

    # 4.6 – validare comună: produsul diabetic trebuie să aibă max. 300 calorii.
    def clean(self):
        date_curate = super().clean()
        if date_curate.get('pt_diabetici') and date_curate.get('calorii', 0) > 300:
            self.add_error('calorii', 'Un produs pentru diabetici trebuie să aibă cel mult 300 calorii per porție.')
        return date_curate

    # 4.10 – save(commit=False) permite calcularea coloanei pret înainte de salvare.
    def save(self, commit=True):
        produs = super().save(commit=False)
        cost = self.cleaned_data['cost_preparare']
        adaos = self.cleaned_data['adaos_procent']
        produs.pret = (cost * (Decimal('1') + adaos / Decimal('100'))).quantize(Decimal('0.01'))
        if commit:
            produs.save()
            self.save_m2m()
        return produs
