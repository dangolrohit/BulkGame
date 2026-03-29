from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("", include("accounts.urls")),
    path("tools/", include("tools.urls")),
    path("channels/", include("channels.urls")),
    path("billing/", include("billing.urls")),
    path("admin-panel/", include("adminpanel.urls")),
    path("api/fb-remover/", include("fb_remover.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
