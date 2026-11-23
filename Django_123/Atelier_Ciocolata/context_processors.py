from django.conf import settings


# LAB 2, TASK 2, SUBPUNCTUL 6: transmite datele firmei și IP-ul în toate template-urile.
def company_context(request):
    return {
        "firma": settings.COMPANY_INFO,
        "ip_client": getattr(request, "ip_client", "Necunoscut"),
    }
