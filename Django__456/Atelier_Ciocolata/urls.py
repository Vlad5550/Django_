from django.urls import path
from . import views

# URL-urile pentru QuerySets (produse/categorii), Lab 5 (contact/mesaje/adauga-produs)
# și paginile deja existente ale proiectului.
urlpatterns = [
    path('', views.index, name='index'),
    path('info', views.info, name='info'),
    path('log', views.log, name='log'),
    path('despre', views.despre, name='despre'),
    path('istoric', views.istoric, name='istoric'),
    path('produse/', views.produse, name='produse'),
    path('produse/<int:pk>/', views.produs_detaliu, name='produs_detaliu'),
    path('categorii/<str:nume_categorie>/', views.categorie_produse, name='categorie_produse'),
    path('contact/', views.contact, name='contact'),
    path('departamente-pentru-tip/', views.departamente_pentru_tip, name='departamente_pentru_tip'),
    path('mesaje/', views.mesaje, name='mesaje'),
    path('adauga-produs/', views.adauga_prajitura, name='adauga_prajitura'),
    path('cos_virtual', views.in_lucru, name='cos_virtual'),
    path('accesare<int:id>', views.detalii_accesare, name='accesare'),
]
