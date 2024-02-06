from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from water_meter import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet, basename='user')

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
   path('admin/', admin.site.urls),
   path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('', include(router.urls)),
   path('search/', views.get_search_addresses, name='addresses-search-list'),

   path('address/<int:address_id>/images/update', views.update_image_address, name='update-image-address'),
   path('address/<int:address_id>/images/get', views.get_image_address, name='get-image-address'),
   path('addresses/', views.get_list_addresses, name='addresses-list'),
   path('addresses/post/', views.post_list_address, name='address-post'),
   path('address/<int:address_id>/', views.detail_address, name='address-detail'),
   path('address/<int:address_id>/update/', views.update_address, name='address-update'),
 
   path('applications/', views.get_list_applications, name='applications-list'),
   path('application/user/', views.get_list_user_application, name='application-user'),
   path('application/<int:water_meter_reading_id>/', views.detail_application, name='application-detail'),
   path('application/<int:water_meter_reading_id>/user/put/', views.put_status_user_application, name='applications-user-put'),
   path('application/<int:water_meter_reading_id>/moderator/put/', views.put_status_moderator_application, name='applications-moderator-put'),
 
   path('manytomany/async/put/', views.put_async_application, name='applications-async-put'),
   path('manytomany/<int:address_id>/', views.delete_address_from_applications, name='manytomanys-delete'),
 
   path('login/',  views.login_view, name='login'),
   path('logout/', views.logout_view, name='logout'),
   path('reg/',  views.register, name='reg'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)