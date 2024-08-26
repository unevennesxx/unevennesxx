from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),  # Asegúrate de que el admin sólo esté bajo 'admin/'
    path("", include("links.urls")),  # Incluye las URLs de tu app 'links' bajo 'cuenta/'
    path('login/', auth_views.LoginView.as_view(), name='login'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)