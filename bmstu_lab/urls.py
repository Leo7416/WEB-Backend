from django.contrib import admin
from django.urls import path
from water_meter import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.GetApplications),
    path('application/<int:address_id>/', views.GetApplication, name='application_url'),
    path('query', views.GetQuery, name='query'),
    path('logical_delete/<int:address_id>/', views.Logical_delete_address, name='logical_delete_url'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)