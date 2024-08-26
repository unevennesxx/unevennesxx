from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class BackupLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    last_backup = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username} - Last Backup: {self.last_backup}"

class LinkQuerySet(models.QuerySet):
    def delete(self):
        if self.count() > 1:
            raise ValidationError("No puedes eliminar multiples links")
        return super().delete()

class Link(models.Model):
    SAMPILICIOUS = 'Samplicious'
    SPECTRUM = 'Spectrum'
    CINT = 'Cint'
    PROGEDE = 'Progede'
    SAMPLE_CUBE = 'Sample-cube'
    INVITE = 'Invite'
    INTERNOS = 'Internos'

    TIPO_CHOICES = [
        (SAMPILICIOUS, 'Samplicious'),
        (SPECTRUM, 'Spectrum'),
        (CINT, 'Cint'),
        (PROGEDE, 'Progede'),
        (SAMPLE_CUBE, 'Sample-cube'),
        (INVITE, 'Invite'),
        (INTERNOS, 'Internos'),
    ]

    nombre = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    fecha_de_agregado = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default=SAMPILICIOUS)
    comentario = models.TextField(blank=True, null=True)


    objects = LinkQuerySet.as_manager()

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

class LoginAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    attempt_time = models.DateTimeField(default=timezone.now)
    successful = models.BooleanField(default=False)  # Indica si el intento fue exitoso o no

    def __str__(self):
        return f"{self.user.username} - {self.attempt_time} - {'Success' if self.successful else 'Failure'}"


