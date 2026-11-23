from django.urls import path, re_path
from . import views
 
# LAB 1-2: rutele paginilor; LAB 2: ruta numerică este definită cu re_path.
urlpatterns = [
    path('', views.index, name='index'),
    path('info', views.info, name='info'),
    path('log', views.log, name='log'),
    path('despre', views.despre, name='despre'),
    path('istoric', views.istoric, name='istoric'),
    path('produse', views.in_lucru, name='produse'),
    path('contact', views.in_lucru, name='contact'),
    path('cos_virtual', views.in_lucru, name='cos_virtual'),
    # re_path permite /accesare2 și /accesare/2 (cu sau fără / final).
    re_path(r'^accesare/?(?P<id>[0-9]+)/?$', views.detalii_accesare, name='accesare'),
    path('liste', views.afiseaza_liste, name='afiseaza_liste'),  # opțional
    path('operatii', views.operatii, name='operatii'),          # opțional
]
