from django.contrib.sessions.models import Session
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from datetime import timedelta

class LimitLoginMiddleware:
    LOCKOUT_TIME = timedelta(minutes=10)  # Tiempo de bloqueo (10 minutos)
    MAX_SESSIONS = 2  # Máximo de sesiones permitidas

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now()

            # Verificar si el usuario está bloqueado
            lockout_time_str = request.session.get('lockout_time')
            if lockout_time_str:
                try:
                    lockout_time = timezone.datetime.fromisoformat(lockout_time_str)
                except ValueError:
                    # Manejar el caso en que el formato de la fecha no es correcto
                    lockout_time = None

                if lockout_time and now < lockout_time:
                    remaining_time = (lockout_time - now).total_seconds()
                    # Redirigir al usuario al login con un mensaje de error
                    return HttpResponseRedirect(f"{reverse('login')}?error=lockout&remaining_time={int(remaining_time)}")

                # Eliminar el tiempo de bloqueo si ya expiró
                if lockout_time:
                    del request.session['lockout_time']

            # Obtener sesiones activas del usuario actual
            user_id = str(request.user.id)
            active_session_keys = set()

            # Obtener sesiones activas del usuario actual
            sessions = Session.objects.filter(expire_date__gte=now)
            for session in sessions:
                session_data = session.get_decoded()
                if str(session_data.get('_auth_user_id')) == user_id:
                    active_session_keys.add(session.session_key)

            # Limitar a un máximo de 2 sesiones
            if len(active_session_keys) > self.MAX_SESSIONS:
                # Cerrar todas las sesiones activas del usuario, excepto la actual
                for session_key in active_session_keys:
                    if session_key != request.session.session_key:
                        Session.objects.filter(session_key=session_key).delete()

                # Establecer el tiempo de bloqueo
                request.session['lockout_time'] = now.isoformat()

                # Redirigir al usuario al login con un mensaje de error
                return HttpResponseRedirect(f"{reverse('login')}?error=max_sessions")

        response = self.get_response(request)
        return response