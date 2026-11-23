from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # LAB 1, CERINȚA 1: aplicația Atelier_Ciocolata este inclusă la rădăcina proiectului.
    path("", include("Atelier_Ciocolata.urls")),
]

# LAB 3, TASK 1, SUBPUNCTUL 12: permite afișarea imaginilor încărcate în dezvoltare.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
