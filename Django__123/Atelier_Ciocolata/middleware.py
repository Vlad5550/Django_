def get_ip(request):
    # Dacă există proxy, păstrăm ultimul IP din antet; altfel folosim IP-ul direct.
    lista_ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if lista_ip:
        return lista_ip.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR', '')


# LAB 1 - cerința 8; LAB 2 - înregistrează fiecare pagină vizitată.
class MiddlewareNou:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .views import Accesare, accesari

        request.ip_client = get_ip(request)

        # Nu înregistrăm fișiere statice, media sau paginile de administrare.
        if not request.path.startswith(('/admin/', '/static/', '/media/')):
            parametri = {
                nume: valori if len(valori) > 1 else (valori[0] if valori else None)
                for nume, valori in request.GET.lists()
            }
            request.accesare = Accesare(
                ip_client=request.ip_client,
                url=request.build_absolute_uri(),
                parametri=parametri,
            )
            accesari.append(request.accesare)
            print(request.accesare)

        return self.get_response(request)
