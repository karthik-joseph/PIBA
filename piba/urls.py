from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from users.views import HomeView

urlpatterns = [
    # Homepage
    path('', HomeView.as_view(), name='home'),
    
    # Django Admin (renamed to avoid conflict with custom admin)
    path('django-admin/', admin.site.urls),

    # User routes (both API and template)
    path('', include('users.urls')),
    
    # Pet routes
    path('', include('pets.urls')),
    
    # Seller routes
    path('', include('sellers.urls')),
    
    # Order routes
    path('', include('orders.urls')),
    
    # Review routes
    path('', include('reviews.urls')),
    
    # Adoption routes
    path('', include('adoption.urls')),
    
    # Custom Admin Dashboard
    path('admin-panel/', include('custom_admin.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
