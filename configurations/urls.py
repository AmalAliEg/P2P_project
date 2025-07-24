
#P2P_project/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_spectacular.utils import extend_schema

TokenObtainPairView = extend_schema(
    tags=['Authentication'],
    operation_id='token_obtain_pair'
)(TokenObtainPairView)

# In your project's urls.py:
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/p2p/', include('p2p_trading.urls')),
    path('api-auth/', include('rest_framework.urls')),
    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

