from .views import Accesare, ACCESARI


# LAB 1, 8;   LAB 2, 2:
# Obține IP-ul din X-Forwarded-For sau REMOTE_ADDR.
def get_ip(request):
    lista_ip = request.META.get("HTTP_X_FORWARDED_FOR")
    if lista_ip:
        return lista_ip.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR", "Necunoscut")


class AccesariMiddleware:
    # LAB 1,  4; LAB 2, 1, 1:
    # Creează și memorează o instanță Accesare pentru fiecare pagină vizitată.
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.ip_client = get_ip(request)

        # Nu înregistrăm fișiere statice, media și paginile admin.
        if request.method == "GET" and not request.path.startswith(("/static/", "/media/", "/admin/", "/favicon")):
            accesare = Accesare(
                request.ip_client,
                request.build_absolute_uri(),
                request.GET.copy(),
            )
            request.accesare = accesare
            ACCESARI.append(accesare)

            # datele accesării apar în consola serverului.
            print(accesare)

        return self.get_response(request)
