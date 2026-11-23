from django.conf import settings
from .models import Categorie


# QUERYSETS 8: meniul primește automat doar categoriile care au cel puțin un produs.
def procesare(request):
    return {
        'firma': settings.FIRMA,
        'copyright': f"© {settings.FIRMA['nume']}" ,
        'ip_client': getattr(request, 'ip_client', ''),
        'categorii_meniu': Categorie.objects.filter(prajituri__isnull=False).distinct(),
    }
