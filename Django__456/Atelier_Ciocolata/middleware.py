def get_ip(request):
    req_headers = request.META
    str_lista_ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if str_lista_ip:
        return str_lista_ip.split(',')[-1].strip()
    else:
        return request.META.get('REMOTE_ADDR')


class MiddlewareNou:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .views import Accesare, accesari

        request.ip_client = get_ip(request)
        if not request.path.startswith(('/admin/', '/static/', '/media/')):
            parametri = {
                cheie: valori if len(valori) > 1 else (valori[0] if valori else None)
                for cheie, valori in request.GET.lists()
            }
            request.accesare = Accesare(
                ip_client=request.ip_client,
                url=request.build_absolute_uri(),
                parametri=parametri,
            )
            accesari.append(request.accesare)
            print(request.accesare)
        return self.get_response(request)

