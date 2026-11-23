from django.urls import path, re_path
from . import views

# LAB 1, CERINȚELE 2 și 10: rutele pentru pagina principală și /info.
# LAB 2, TASK 1: jurnal, istoric, despre și detaliile unei accesări.
# LAB 2, TASK 2, SUBPUNCTUL 10: rutele paginilor încă neimplementate.
urlpatterns = [
    path("", views.index, name="index"),
    path("info", views.info, name="info"),
    path("log", views.log, name="log"),
    path("despre", views.despre, name="despre"),
    path("istoric", views.istoric, name="istoric"),
    path("produse", views.in_lucru, {"titlu": "Produse"}, name="produse"),
    path("contact", views.in_lucru, {"titlu": "Contact"}, name="contact"),
    path("cos_virtual", views.in_lucru, {"titlu": "Coș virtual"}, name="cos_virtual"),
    # LAB 2, TASK 1, SUBPUNCTUL 5: rută regex /accesare<ID numeric>.
    path("accesare/<int:id>/", views.accesare_id, name="accesare_id"),
 
]
