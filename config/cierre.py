# middleware.py
from django.utils import timezone
from django.contrib.auth.signals import user_logged_out
from .models import LoginAttempt

class RecordLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

def record_logout(sender, request, user, **kwargs):
    LoginAttempt.objects.create(
        user=user,
        attempt_time=timezone.now(),
        successful=False
    )

user_logged_out.connect(record_logout)
