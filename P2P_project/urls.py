"""
URL configuration for P2P_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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

#P2P_project/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="P2P Trading API",
        default_version='v1',
        description="P2P Trading Platform",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# In your project's urls.py:
# path('api/p2p/', include('p2p_trading.urls')),
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/p2p/', include('p2p_trading.urls')),
    path('api/auth/', include('MainDashboard.urls')),
    path('api-auth/', include('rest_framework.urls')),
    # Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)