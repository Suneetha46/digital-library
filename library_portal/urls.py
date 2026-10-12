"""
URL configuration for library_portal project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Custom admin branding
admin.site.site_header = "Digital Library & E-Book Portal Admin"
admin.site.site_title = "Digital Library Admin"
admin.site.index_title = "Library Circulation & Catalog Management"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('circulation.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
