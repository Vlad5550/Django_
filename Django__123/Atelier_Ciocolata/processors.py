from django.conf import settings


# LAB 2, Task 2 - cerința 6: trimite datele firmei și IP-ul în toate template-urile.
def procesare(request):
    firma = settings.FIRMA
    return {
        'firma': firma,
        'copyright': f"© {firma['nume']}",
        'ip_client': getattr(request, 'ip_client', ''),
    }
