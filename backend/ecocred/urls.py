from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from backend.views import backend_home

urlpatterns = [
    path("", backend_home),
    path("api/auth/", include("backend.users.urls")),
    path("api/waste/", include("backend.waste.urls")),
    path("api/rewards/", include("backend.rewards.urls")),
    path("api/aggregators/", include("backend.aggregators.urls")),
    path("api/recyclers/", include("backend.recyclers.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
