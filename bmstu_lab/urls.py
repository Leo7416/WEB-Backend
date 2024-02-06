from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from water_meter import views 

router = routers.DefaultRouter()

urlpatterns = [
    path('admin/', admin.site.urls),
 
    path('', views.GetApplications),
    path('application/<int:address_id>/', views.GetApplication, name='application_url'),
    path('query', views.GetQuery, name='query'),
    path('logical_delete/<int:address_id>/', views.Logical_delete_address, name='logical_delete_url'),
    path('', include(router.urls)),

    path('search/', views.get_search_addresses, name='addresses-search-list'),
    path('addresses/', views.get_list_addresses, name='addresses-list'),
    path('address/post/', views.post_list_address, name='address-post'),
    path('address/<int:address_id>/', views.detail_address, name='address-detail'),
    path('address/<int:address_id>/images', views.get_image_address, name='address-images'),
    path('applications/', views.get_list_applications, name='applications-list'),
    path('application/<int:water_application_reading_id>/', views.detail_application, name='application-detail'),
    path('application/<int:water_application_reading_id>/user/put/', views.put_status_user_application, name='applications-user-put'),
    path('application/<int:water_application_reading_id>/moderator/put/', views.put_status_moderator_application, name='applications-moderator-put'),
    path('manytomany/<int:many_id>/', views.delete_address_from_applications, name='manytomanys-delete'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)