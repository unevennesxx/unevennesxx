from django import forms
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import admin
from django.utils.html import format_html
from django.core.serializers import serialize
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.admin.sites import site
from django.contrib.sessions.models import Session
import json
import os
from .models import Link
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Q
import re
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class ImportForm(forms.Form):
    file = forms.FileField()

class BackupForm(forms.Form):
    file = forms.FileField()

class LinkAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'short_url', 'tipo', 'fecha_de_agregado_with_icon', 'short_comentario')
    list_filter = ('tipo', 'fecha_de_agregado')
    search_fields = ('nombre', 'url')
    ordering = ('-fecha_de_agregado',)
    change_list_template = 'admin/change_list.html'
    list_per_page = 10

    def short_url(self, obj):
        full_url = obj.url
        displayed_url = full_url if len(full_url) <= 50 else full_url[:47] + '...'
        return format_html(
            '''
            <div class="url-field" onclick="copyToClipboard('{}')" style="cursor: pointer;" title="Click to copy full URL">
                {}
            </div>
            <script>
            function copyToClipboard(url) {{
                navigator.clipboard.writeText(url).then(function() {{
                    alert("URL copied to clipboard: " + url);
                }}, function(err) {{
                    console.error("Could not copy text: ", err);
                }});
            }}
            </script>
            ''',
            full_url, displayed_url
        )
    short_url.short_description = 'URL'

    def short_comentario(self, obj):
        full_comentario = obj.comentario or ""
        displayed_comentario = full_comentario if len(full_comentario) <= 30 else full_comentario[:27] + '...'
        return format_html(
            '''
            <div class="comentario-field" onclick="showFullComentario('{}')" style="cursor: pointer;" title="Click to view full comment">
                {}
            </div>
            <script>
            function showFullComentario(comentario) {{
                alert("Full comment: " + comentario);
            }}
            </script>
            ''',
            full_comentario, displayed_comentario
        )
    short_comentario.short_description = 'Comentario'

    def fecha_de_agregado_with_icon(self, obj):
        formatted_date = obj.fecha_de_agregado.strftime('%d/%m/%Y')
        return format_html(
            '''
            <div style="display: flex; align-items: center;">
                <span id="icon-{}" title="Click to show date" style="cursor: pointer; font-size: 1.2em; color: #007bff;" onclick="showDateAndHideIcon('icon-{}', 'date-{}')">👁️</span>
                <span id="date-{}" style="display: none;">{}</span>
            </div>
            <script>
            function showDateAndHideIcon(iconId, dateId) {{
                var dateElement = document.getElementById(dateId);
                var iconElement = document.getElementById(iconId);
                dateElement.style.display = 'inline';
                iconElement.style.display = 'none';
            }}
            </script>
            ''',
            obj.pk, obj.pk, obj.pk, obj.pk, formatted_date
        )
    fecha_de_agregado_with_icon.short_description = 'Fecha'

    def normalize_string(self, string):
        if string:
            string = re.sub(r'^https?://', '', string)
            string = re.sub(r'^www\.', '', string)
            string = re.sub(r'/.*$', '', string)
            return string.lower()
        return ''

    def get_search_results(self, request, queryset, search_term):
        normalized_search_term = self.normalize_string(search_term)

        queryset = queryset.filter(
            Q(url__icontains=normalized_search_term) |
            Q(nombre__icontains=normalized_search_term)
        )

        search_term_parts = normalized_search_term.split('.')
        if len(search_term_parts) > 1:
            base_domain = '.'.join(search_term_parts[-2:])
            sub_domain = '.'.join(search_term_parts[:-2])

            queryset |= queryset.filter(
                Q(url__icontains=base_domain) |
                Q(nombre__icontains=base_domain) |
                Q(url__icontains=sub_domain) |
                Q(nombre__icontains=sub_domain) |
                Q(url__icontains=search_term) |
                Q(nombre__icontains=search_term)
            )

            if len(search_term_parts) > 2:
                full_domain = '.'.join(search_term_parts[-3:])
                queryset |= queryset.filter(
                    Q(url__icontains=full_domain) |
                    Q(nombre__icontains=full_domain)
                )

        return queryset, False

    def export_as_json(self, request, queryset):
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename=links.json'
        
        data = serialize('json', queryset)
        json_data = json.loads(data)
        
        json_response = json.dumps(json_data, cls=DateTimeEncoder)
        response.write(json_response)
        
        return response

    export_as_json.short_description = 'Export Selected as JSON'

    def import_json(self, request):
        if request.method == 'POST':
            form = ImportForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                data = file.read().decode('utf-8')
                json_data = json.loads(data)
                
                for obj_data in json_data:
                    obj, created = Link.objects.update_or_create(
                        nombre=obj_data['fields']['nombre'],
                        defaults={
                            'url': obj_data['fields']['url'],
                            'fecha_de_agregado': obj_data['fields']['fecha_de_agregado'],
                            'tipo': obj_data['fields']['tipo'],
                            'comentario': obj_data['fields'].get('comentario', ''),
                        }
                    )
                
                self.message_user(request, "Your JSON file has been imported.")
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = ImportForm()

        return render(request, 'admin/import_form.html', {'form': form})

    import_json.short_description = 'Import JSON'

    def backup_data(self, request):
        if request.method == 'POST':
            form = BackupForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['file']
                file_path = os.path.join(settings.MEDIA_ROOT, 'backups', file.name)
                
                with default_storage.open(file_path, 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)

                self.message_user(request, "Backup file has been uploaded.")
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = BackupForm()

        return render(request, 'admin/backup_form.html', {'form': form})

    backup_data.short_description = 'Upload Backup'

    def download_backup(self, request):
        file_path = os.path.join(settings.MEDIA_ROOT, 'backups', 'backup.zip')
        
        if default_storage.exists(file_path):
            with default_storage.open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename={os.path.basename(file_path)}'
                return response
        
        self.message_user(request, "Backup file not found.", level='error')
        return HttpResponseRedirect(request.get_full_path())

    download_backup.short_description = 'Download Backup'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('import-json/', self.admin_site.admin_view(self.import_json), name='import_json'),
            path('backup-upload/', self.admin_site.admin_view(self.backup_data), name='backup_upload'),
            path('backup-download/', self.admin_site.admin_view(self.download_backup), name='backup_download'),
            path('active-users/', self.admin_site.admin_view(self.active_users_view), name='active_users'),
        ]
        return custom_urls + urls

    def delete_queryset(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Bulk deletion is not allowed", level='error')
            return
        try:
            super().delete_queryset(request, queryset)
        except ValidationError as e:
            self.message_user(request, str(e), level='error')

    def changelist_view(self, request, extra_context=None):
        if request.path == '/admin/':
            return redirect('/links/link/')
        
        if 'q' in request.GET:
            search_term = request.GET['q']
            if re.search(r'\.com$', search_term, re.IGNORECASE):
                search_message = "Busquedas mejoradas sin .COM: Los resultados de búsqueda también coinciden con variaciones de dominio sin .com."
            else:
                search_message = "Busquedas mejoradas: Los resultados de búsqueda incluyen variaciones como www., https://, etc."

            if extra_context is None:
                extra_context = {}
            extra_context['search_message'] = search_message

        return super().changelist_view(request, extra_context=extra_context)

    actions = [export_as_json]

    def active_users_view(self, request):
        active_sessions = Session.objects.filter(expire_date__gte=datetime.now())
        user_ids = [session.get_decoded().get('_auth_user_id') for session in active_sessions if session.get_decoded().get('_auth_user_id')]
        users = User.objects.filter(id__in=user_ids)
        
        return render(request, 'admin/active_users.html', {'users': users})

    active_users_view.short_description = 'Active Users'

admin.site.unregister(Group)

class UserAdmin(DefaultUserAdmin):
    def has_add_permission(self, request):
        return request.user.username in ['admin', 'jennifer', 'roberth98']

    def has_delete_permission(self, request, obj=None):
        return request.user.username == 'admin'

    def get_model_perms(self, request):
        if request.user.username not in ['admin', 'jennifer', 'roberth98']:
            return {}
        return super().get_model_perms(request)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Link, LinkAdmin)

class CustomAdminSite(admin.AdminSite):
    def get_model_permissions(self, request):
        if request.user.username in ['admin', 'jennifer', 'roberth98']:
            return super().get_model_permissions(request)
        else:
            return {model: perms for model, perms in super().get_model_permissions(request).items() if model != User}

custom_admin_site = CustomAdminSite()
custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(Link, LinkAdmin)

admin.site = custom_admin_site
