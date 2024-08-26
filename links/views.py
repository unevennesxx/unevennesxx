import os
import glob
import datetime
from io import StringIO
from django import forms
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.core.management import call_command
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_exempt
import logging
import io  # Importa io si no lo habías importado antes

logger = logging.getLogger(__name__)

# Formulario para buscar backups por fecha
class DateSearchForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)

@login_required
def backup_restore_view(request):
    # Solo permitir a usuarios con nombre 'admin'
    if request.user.username != 'admin':
        return HttpResponse("No tiene permisos para realizar esta acción")

    form = DateSearchForm(request.GET or None)

    if not settings.BACKUP_ROOT:
        logger.error("BACKUP_ROOT is not configured in settings.")
        messages.error(request, "BACKUP_ROOT is not configured. Please contact the administrator.")
        return redirect("backup-restore")

    backups = glob.glob(os.path.join(settings.BACKUP_ROOT, '*.json'))
    list_backups = []
    for backup in backups:
        list_backups.append({
            "name": os.path.basename(backup),
            "date": os.path.basename(backup)[7:17],
            "time": os.path.basename(backup)[18:26].replace("-", ":")
        })

    if form.is_valid():
        search_date = form.cleaned_data['date']
        if search_date:
            list_backups = [b for b in list_backups if b['date'] == search_date.strftime('%d-%m-%Y')]

    if request.method == 'POST':
        if 'backup' in request.POST:
            try:
                create_backup(request)  # Pasar el argumento request
                messages.success(request, "Copia de seguridad creada correctamente.")
            except Exception as e:
                logger.error(f"Error al crear el backup: {e}")
                messages.error(request, "No se pudo crear la copia de seguridad.")
            return redirect("backup-restore")
        elif 'restore' in request.POST:
            filename = request.POST.get("filename")
            if not filename:
                messages.error(request, "Debe seleccionar un archivo de backup para restaurar.")
                return redirect("backup-restore")
            filepath = os.path.join(settings.BACKUP_ROOT, filename)
            try:
                call_command('loaddata', filepath)
                messages.success(request, "Copia de seguridad restaurada correctamente.")
            except Exception as e:
                logger.error(f"Error al restaurar el backup: {e}")
                messages.error(request, f"Error al restaurar la copia de seguridad: {e}")
            return redirect("backup-restore")

    return render(request, 'admin/respaldo.html', {"backups": list_backups, "form": form})

@login_required
def create_backup(request):  # Añadir request como parámetro
    buf = StringIO()
    call_command('dumpdata', 'links.Link', stdout=buf)  # Reemplaza 'links' por el nombre de tu aplicación
    buf.seek(0)
    datetime_backup = datetime.datetime.now()  # Usa datetime.datetime.now() si has importado la clase datetime directamente
    backup_filename = "backup-" + datetime_backup.strftime('%d-%m-%Y_%H-%M-%S') + ".json"
    backup_path = os.path.join(settings.BACKUP_ROOT, backup_filename)
    with open(backup_path, 'w', encoding='utf8') as f:
        f.write(buf.read())

    # Registrar en el log la creación del backup
    logger.info(f"Backup created: {backup_filename} by user {request.user.username}")

@login_required
def download_backup(request, filename):
    # Solo permitir a usuarios con nombre 'admin'
    if request.user.username != 'admin':
        return HttpResponse("No tiene permisos para realizar esta acción")

    file_path = os.path.join(settings.BACKUP_ROOT, filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
            return response
    else:
        logger.error(f"File not found: {file_path}")
        raise Http404("File not found")

@login_required
def upload_backup(request):
    # Solo permitir a usuarios con nombre 'admin'
    if request.user.username != 'admin':
        return HttpResponse("No tiene permisos para realizar esta acción")

    if request.method == 'POST' and 'backup_file' in request.FILES:
        backup_file = request.FILES['backup_file']
        if not backup_file.name.endswith('.json'):
            messages.error(request, 'Solo se permiten archivos .json.')
            return redirect('backup-restore')
        try:
            fs = FileSystemStorage(location=settings.BACKUP_ROOT)
            filename = fs.save(backup_file.name, backup_file)
            messages.success(request, 'Backup subido con éxito.')
        except Exception as e:
            logger.error(f"Error al subir el backup: {e}")
            messages.error(request, f"Error al subir la copia de seguridad: {e}")
        return redirect('backup-restore')
    return render(request, 'admin/restaurar.html')

@csrf_exempt
def index(request):
    return render(request, 'registration/login.html', {})

@csrf_exempt
def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('/admin/')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
def extract_links_to_txt(request):
    try:
        # Obtener todos los registros de Link desde la base de datos
        links = Link.objects.all()

        # Crear un archivo en memoria usando io.StringIO
        output = io.StringIO()

        # Preparar los datos para escribir en el archivo .txt
        for link in links:
            # Formatear la fecha
            if link.fecha_de_agregado:
                formatted_date = link.fecha_de_agregado.strftime('%d, %B, %Y. %I:%M %p')
            else:
                formatted_date = 'Fecha no disponible'

            output.write(f"Nombre: {link.nombre}\n")
            output.write(f"URL: {link.url}\n")
            output.write(f"Tipo de Survey: {link.get_tipo_display()}\n")  # Incluir el tipo de survey
            output.write(f"Fecha: {formatted_date}\n")
            output.write(f"Comentario: {link.comentario if link.comentario else 'N/A'}\n")
            output.write("\n----------------\n")

        # Crear la respuesta HTTP con el archivo adjunto
        response = HttpResponse(output.getvalue(), content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="links_extraidos.txt"'
        
        return response
    except Exception as e:
        logger.error(f"Error al extraer enlaces: {e}")
        messages.error(request, "Ocurrió un error al intentar extraer los enlaces.")
        return redirect('extraer-links-html')

@login_required
def extraer_links_html(request):
    return render(request, 'admin/extraer_links.html')

from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from pytz import timezone as pytz_timezone
from .models import Link, LoginAttempt

User = get_user_model()

@login_required
def active_users_view(request):
    # Zona horaria de Venezuela
    venezuela_tz = pytz_timezone('America/Caracas')

    # Filtrar las sesiones activas
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_ids = [session.get_decoded().get('_auth_user_id') for session in active_sessions if session.get_decoded().get('_auth_user_id')]
    users = User.objects.filter(id__in=user_ids)

    # Obtener el último enlace agregado
    latest_link = Link.objects.latest('fecha_de_agregado') if Link.objects.exists() else None

    # Calcular la duración diaria para cada usuario
    user_data = []
    today = timezone.now().date()
    
    for user in users:
        # Obtener todos los intentos de inicio de sesión y cierre de sesión
        login_attempts = LoginAttempt.objects.filter(user=user, successful=True).order_by('attempt_time')
        logout_attempts = LoginAttempt.objects.filter(user=user, successful=False).order_by('attempt_time')

        # Filtrar intentos de inicio y cierre de sesión del día actual
        login_attempts_today = login_attempts.filter(attempt_time__date=today)
        logout_attempts_today = logout_attempts.filter(attempt_time__date=today)

        # Calcular la duración diaria
        active_duration = timezone.timedelta()
        for login_attempt in login_attempts_today:
            corresponding_logout = logout_attempts_today.filter(attempt_time__gt=login_attempt.attempt_time).first()
            if corresponding_logout:
                active_duration += corresponding_logout.attempt_time - login_attempt.attempt_time
            else:
                active_duration += timezone.now() - login_attempt.attempt_time

        active_days = active_duration.days
        active_hours, remainder = divmod(active_duration.seconds, 3600)
        active_minutes, _ = divmod(remainder, 60)
        
        # Convertir las fechas a la zona horaria de Venezuela y formatear en 12 horas
        def format_datetime(dt):
            if dt:
                dt = dt.astimezone(venezuela_tz)
                return dt.strftime("%d/%m/%Y %I:%M %p")
            return 'Nunca ha iniciado sesión'

        last_login_attempt = login_attempts.last()
        last_login = format_datetime(last_login_attempt.attempt_time) if last_login_attempt else 'Nunca ha iniciado sesión'

        last_logout_attempt = logout_attempts.last()
        last_logout = format_datetime(last_logout_attempt.attempt_time) if last_logout_attempt else 'Nunca ha cerrado sesión'

        # Convertir el último inicio de sesión a timestamp Unix
        last_login_timestamp = int(last_login_attempt.attempt_time.timestamp()) if last_login_attempt else None

        user_data.append({
            'username': user.username,
            'email': user.email,
            'last_login': last_login,
            'last_logout': last_logout,
            'last_login_timestamp': last_login_timestamp,
            'active_days': active_days,
            'active_hours': active_hours,
            'active_minutes': active_minutes,
        })

    # Calcular el tiempo desde que se agregó el último enlace
    if latest_link:
        time_since_last_link = timezone.now() - latest_link.fecha_de_agregado
        days = time_since_last_link.days
        hours, remainder = divmod(time_since_last_link.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_since_last_link_str = f"{days} días, {hours} horas, {minutes} minutos" if days else f"{hours} horas, {minutes} minutos"
    else:
        time_since_last_link_str = "N/A"

    # Calcular la cantidad de enlaces agregados hoy, este mes y este año
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)

    links_today = Link.objects.filter(fecha_de_agregado__date=today).count()
    links_this_month = Link.objects.filter(fecha_de_agregado__gte=start_of_month).count()
    links_this_year = Link.objects.filter(fecha_de_agregado__gte=start_of_year).count()

    # Preparar datos para la plantilla
    context = {
        'users': user_data,
        'latest_link': latest_link,
        'time_since_last_link': time_since_last_link_str,
        'links_today': links_today,
        'links_this_month': links_this_month,
        'links_this_year': links_this_year,
    }

    return render(request, 'admin/active_users.html', context)
