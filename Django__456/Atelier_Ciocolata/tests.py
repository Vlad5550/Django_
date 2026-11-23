from datetime import datetime

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import resolve, reverse

from . import views
from .models import (
    Ambalaj, Categorie, Eveniment, IstoricPret, Organizator,
    Prajitura, PrajituriEvenimente, SediuEveniment,
)


@override_settings(ALLOWED_HOSTS=['testserver'])
class PaginiTests(TestCase):
    def setUp(self):
        views.accesari.clear()
        views.Accesare.urmatorul_id = 1

    def test_pagina_principala_cinci_sectiuni(self):
        raspuns = self.client.get('/')
        self.assertEqual(raspuns.status_code, 200)
        self.assertContains(raspuns, views.DESCRIERE)
        for nume in ('prezentare', 'specialitati', 'servicii', 'ambalaje', 'evenimente'):
            self.assertContains(raspuns, f'<section id="{nume}">')

    def test_info_si_data_romana(self):
        raspuns = self.client.get('/info')
        self.assertEqual(raspuns.status_code, 200)
        self.assertContains(raspuns, '<title>Informații despre server</title>')
        self.assertContains(raspuns, '<h1>Informații despre server</h1>')
        self.assertContains(raspuns, '<h2>Data și ora</h2>')
        self.assertTrue(any(zi in raspuns.context['sectiune'] for zi in views.ZILE))

    def test_info_numai_data(self):
        sectiune = self.client.get('/info?data=zi').context['sectiune']
        self.assertIn('Data și ora', sectiune)
        self.assertNotIn(':', sectiune)

    def test_info_numai_ora(self):
        sectiune = self.client.get('/info?data=timp').context['sectiune']
        self.assertRegex(sectiune, r'\d{2}:\d{2}:\d{2}')
        self.assertFalse(any(luna in sectiune for luna in views.LUNI))

    def test_accesare_data_metode(self):
        data = datetime(2025, 10, 2, 13, 4, 5)
        accesare = views.Accesare('127.0.0.1', 'http://testserver/info?a=1&b=',
                                  {'a': '1', 'b': None}, data=data)
        self.assertEqual(accesare.id, 1)
        self.assertEqual(accesare.pagina(), '/info')
        self.assertEqual(accesare.string_url(), 'http://testserver/info?a=1&b=')
        self.assertEqual(accesare.lista_parametri(), [('a', '1'), ('b', None)])
        self.assertIn('Joi, 2 Octombrie 2025', accesare.calculeaza_data())
        self.assertIn('2 Octombrie 2025', accesare.calculeaza_data(tip='zi'))
        self.assertIn('13:04:05', accesare.calculeaza_data(tip='timp'))
        self.assertIn('id: 1', str(accesare))
        self.assertEqual(views.Accesare('127.0.0.1', '/').id, 2)

    def test_log_include_propria_cerere(self):
        self.client.get('/')
        raspuns = self.client.get('/log')
        self.assertEqual([a.pagina() for a in raspuns.context['accesari']], ['/', '/log'])

    def test_log_ultimele(self):
        self.client.get('/')
        self.client.get('/info')
        raspuns = self.client.get('/log?ultimele=2')
        self.assertEqual([a.id for a in raspuns.context['accesari']], [2, 3])

    def test_log_ultimele_invalid(self):
        for valoare in ('abc', '-1', '1.5'):
            raspuns = self.client.get('/log', {'ultimele': valoare})
            self.assertTrue(raspuns.context['eroare'])

    def test_log_ultimele_prea_multe(self):
        raspuns = self.client.get('/log?ultimele=5')
        self.assertEqual(len(raspuns.context['accesari']), 1)
        self.assertIn('Exista doar 1 accesari fata de 5 accesari cerute',
                      raspuns.context['eroare'])

    def test_log_iduri_cu_si_fara_dubluri(self):
        for pagina in ('/', '/info', '/despre'):
            self.client.get(pagina)
        raspuns = self.client.get('/log?iduri=2,3&iduri=1,2')
        self.assertEqual([a.id for a in raspuns.context['accesari']], [2, 3, 1])
        raspuns = self.client.get('/log?iduri=2,3&iduri=1,2&dubluri=true')
        self.assertEqual([a.id for a in raspuns.context['accesari']], [2, 3, 1, 2])

    def test_log_numar_si_detalii(self):
        self.client.get('/')
        nr = self.client.get('/log?accesari=nr')
        self.assertEqual(nr.context['numar_accesari'], 2)
        detalii = self.client.get('/log?accesari=detalii')
        self.assertEqual(len(detalii.context['detalii']), 3)
        self.assertContains(detalii, '<h2>Detalii</h2>')

    def test_log_parametri_repetati(self):
        raspuns = self.client.get('/log?iduri=1&iduri=2&dubluri=true')
        self.assertEqual(raspuns.context['numar_parametri'], 3)
        self.assertEqual(raspuns.context['parametri'], ['iduri', 'iduri', 'dubluri'])

    def test_log_tabel(self):
        raspuns = self.client.get('/log?tabel=id,url')
        self.assertEqual(raspuns.context['coloane'], ['id', 'url'])
        self.assertEqual(len(raspuns.context['randuri'][0]), 2)
        raspuns = self.client.get('/log?tabel=tot')
        self.assertEqual(raspuns.context['coloane'], ['id', 'ip_client', 'url', 'parametri', 'data'])

    def test_log_statistici_pagini(self):
        self.client.get('/')
        self.client.get('/')
        self.client.get('/info')
        raspuns = self.client.get('/log')
        self.assertEqual(raspuns.context['pagina_maxima'], '/')
        self.assertEqual(raspuns.context['pagina_minima'], '/info')

    def test_accesare_ruta_si_detalii(self):
        self.client.get('/')
        self.assertEqual(reverse('accesare', args=[1]), '/accesare1')
        raspuns = self.client.get('/accesare1')
        self.assertEqual(raspuns.status_code, 200)
        self.assertContains(raspuns, 'ip_client:')
        self.assertContains(raspuns, 'lista_parametri:')
        self.assertEqual(self.client.get('/accesare999').status_code, 404)

    def test_paginin_sablon_meniu_si_footer(self):
        for pagina in ('/', '/info', '/log', '/despre', '/istoric',
                       '/produse/', '/contact/', '/cos_virtual', '/mesaje/', '/adauga-produs/'):
            raspuns = self.client.get(pagina)
            self.assertEqual(raspuns.status_code, 200)
            self.assertContains(raspuns, '<header>')
            self.assertContains(raspuns, '<main>')
            self.assertContains(raspuns, '<footer>')
            self.assertContains(raspuns, 'Cofetaria Dulcelind')
        self.assertContains(self.client.get('/contact/'), '<h1>Contact</h1>')
        self.assertContains(self.client.get('/cos_virtual'), '<title>In lucru</title>')

    def test_ip_middleware(self):
        raspuns = self.client.get('/', HTTP_X_FORWARDED_FOR='10.0.0.1, 10.0.0.2')
        self.assertContains(raspuns, 'IP: 10.0.0.2')
        self.assertEqual(views.accesari[0].ip_client, '10.0.0.2')

    def test_meniu_submeniu_si_imagini(self):
        pagina = self.client.get('/').content.decode()
        self.assertIn('class="submeniu"', pagina)
        self.assertIn('/static/Atelier_Ciocolata/imagini/ciocolata.svg', pagina)
        pagina = self.client.get('/despre').content.decode()
        self.assertIn('/static/Atelier_Ciocolata/imagini/ciocolata.svg', pagina)

    def test_rute(self):
        self.assertEqual(resolve('/').url_name, 'index')
        rute = {
            '/info': 'info', '/log': 'log', '/despre': 'despre',
            '/istoric': 'istoric', '/produse/': 'produse',
            '/contact/': 'contact', '/cos_virtual': 'cos_virtual',
            '/mesaje/': 'mesaje', '/adauga-produs/': 'adauga_prajitura',
        }
        for ruta, nume in rute.items():
            self.assertEqual(resolve(ruta).url_name, nume)


class ModeleTests(SimpleTestCase):
    def test_modele_si_relatii(self):
        modele = (Categorie, Prajitura, Ambalaj, Organizator,
                  SediuEveniment, Eveniment, IstoricPret)
        self.assertEqual(len(modele), 7)
        self.assertEqual(Prajitura._meta.get_field('categorie').many_to_one, True)
        self.assertEqual(Prajitura._meta.get_field('ambalaje').many_to_many, True)
        self.assertEqual(Eveniment._meta.get_field('prajituri').remote_field.through, PrajituriEvenimente)
        self.assertEqual(IstoricPret._meta.get_field('produs').remote_field.on_delete.__name__, 'CASCADE')

    def test_restrictii_modele(self):
        modele = (Categorie, Prajitura, Ambalaj, Organizator,
                  SediuEveniment, Eveniment, IstoricPret)
        campuri = [f for model in modele for f in model._meta.get_fields()
                   if getattr(f, 'concrete', False)]
        self.assertGreaterEqual(sum(f.null for f in campuri), 5)
        self.assertGreaterEqual(sum(f.unique and not f.primary_key for f in campuri), 1)
        self.assertGreaterEqual(sum(f.has_default() for f in campuri), 4)
        self.assertGreaterEqual(sum(bool(f.help_text) for f in campuri), 5)
        self.assertGreaterEqual(sum(bool(f.error_messages) and any(
            code in f.error_messages for code in ('unique', 'invalid', 'max_length', 'blank'))
            for f in campuri), 5)
        self.assertGreaterEqual(sum(len(model._meta.constraints) for model in modele), 5)
        self.assertGreaterEqual(sum(bool(model._meta.ordering) for model in modele), 2)
        self.assertGreaterEqual(sum(len(model._meta.indexes) for model in modele), 4)


class Laborator5HelpersTests(SimpleTestCase):
    def test_cod_cerere_are_formatul_generat(self):
        import re
        self.assertRegex(views.cod_nou_cerere(), r'^[A-Z]{3}[a-z]{2}[0-9]{8}$')

    def test_mesajul_devine_paragrafe_html(self):
        self.assertEqual(
            views.mesaj_html('salut lume. azi este soare\n al doilea   rand'),
            '<p>salut lume. Azi este soare</p><p>al doilea rand</p>'
        )
