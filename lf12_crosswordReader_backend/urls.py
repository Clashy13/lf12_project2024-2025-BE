"""
URL configuration for lf12_crosswordReader_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from lf12_crosswordReader_backend.views import Overview, ImagePath, UploadImage, Delete
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

router = DefaultRouter()
router.register(r"images", UploadImage)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("crosswords/overview/", Overview.as_view(), name="crossword-overview"),
    path("crosswords/<uuid:pk>/image/", ImagePath.as_view(), name="crossword-detail"),
    path("crosswords/<uuid:pk>/delete/", Delete.as_view(), name="delete-crossword"),
    path("crosswords/upload/", UploadImage.as_view(), name="crossword-upload"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
