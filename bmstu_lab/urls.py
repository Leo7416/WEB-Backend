from django.contrib import admin
from django.urls import path
from water_meter import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.GetOrders),
    path('order/<int:id>/', views.GetOrder, name='order_url'),
    path('query', views.GetQuery, name='query')
]
