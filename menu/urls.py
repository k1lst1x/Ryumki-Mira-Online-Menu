# menu/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.i18n import i18n_patterns

# вне i18n: служебное переключение языка
urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("rosetta/", include("rosetta.urls")),  # только для staff
]

# локализованные маршруты приложения и админка
urlpatterns += i18n_patterns(
    path("admin-django/", admin.site.urls),
    path("", include("menuapp.urls")),
    prefix_default_language=False,  # базовый язык без префикса (/ вместо /ru/)
)

# раздача статики/медиа в DEV (на проде этим должен заниматься сервер)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
