# middleware.py
from django.utils import timezone
from .models import LoginAttempt

class RecordLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated and request.session.get('_auth_user_id'):
            # Registrar el cierre de sesión si se está cerrando
            if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                # Esto es para AJAX; puedes ajustar según tus necesidades
                pass
            else:
                # Registrar cierre de sesión en el modelo
                LoginAttempt.objects.create(
                    user=request.user,
                    attempt_time=timezone.now(),
                    successful=True
                )
        return response

