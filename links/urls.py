from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # Rutas para la gestión de backups
    path('backup/', views.backup_restore_view, name='backup-restore'),
    path('backup/download/<str:filename>/', views.download_backup, name='backup-download'),
    path('backup/upload/', views.upload_backup, name='backup-upload'),

    # Ruta de inicio de sesión personalizada y logout
    path('admin/login/', views.custom_login, name='custom_login'),
    path('login/', views.custom_login, name='custom_login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Rutas para la extracción de enlaces
    path('extraer-links/', views.extract_links_to_txt, name='extraer_links'),
    path('extraer-links-html/', views.extraer_links_html, name='extraer_links_html'),

    # Ruta para mostrar usuarios conectados
    path('active-users/', views.active_users_view, name='active_users'),
    

    # Ruta por defecto de la vista principal
    path('', views.index, name='index'),
]
