from django.http import JsonResponse


def health_check(request):
    """Lightweight liveness endpoint for the container and Traefik healthchecks.

    It does not query the database and does not require login.
    """
    return JsonResponse({'status': 'ok'})
