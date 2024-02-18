from django.db.models import Q
from datetime import date
from django.db.models import Count
from django.shortcuts import render, redirect
from water_meter.models import Addresses, WaterMeterReading, Manytomany, CustomUser
from django.db import connection


def GetApplications(request):
    data = Addresses.objects.filter(Q(address_status='Действует') | Q(address_status='В корзине'))
    return render(request, 'applications.html', {'data': data})

def GetApplication(request, address_id):
    address = Addresses.objects.get(address_id=address_id)
    meter_reading = address.meter_reading
    
    return render(request, 'application.html', {'application': address, 'meter_reading': meter_reading})

        
def GetQuery(request):
    query = request.GET.get('query', '')

    if query.isnumeric():
        filtered_addresses = Addresses.objects.filter(apartment=query)
    else:
        # Если query не является числом, выполняем фильтрацию по полям town и address
        filtered_addresses = Addresses.objects.filter(
            Q(town=query) |
            Q(address=query)
        )
    return render(request, 'applications.html', {'data': filtered_addresses})

def GetMeterReading(request,meter_reading):
    return render(request, 'application.html', {'reading': WaterMeterReading.objects.get(meter_reading=meter_reading)})

def Logical_delete_address(request, address_id):
    # SQL-запрос для изменения статуса записи
    sql = "UPDATE addresses SET address_status = 'Удален' WHERE address_id = %s;"
    
    # Выполняем SQL-запрос
    with connection.cursor() as cursor:
        cursor.execute(sql, [address_id])
    
    # Перенаправляем на корневой URL
    return redirect('')

def AddToCart(request, address_id):
    user = request.user
    
    # Проверяем, существует ли у пользователя черновик операции с определенным статусом
    draft_operation = WaterMeterReading.objects.filter(
        id_user=user,
        meter_status='Черновик'
    ).first()
    
    # Если черновик операции не существует, создаем новый
    if not draft_operation:
        draft_operation = WaterMeterReading.objects.create(
            id_user=user,
            date_creating=date.today(),  # Устанавливаем текущую дату создания
            meter_status='Черновик'
        )
    
    # Проверяем, существует ли уже в черновике указанный адрес
    existing_address = Manytomany.objects.filter(
        address_id=address_id,
        meter_id=draft_operation
    ).exists()
    
    # Если адрес уже есть в черновике, просто перенаправляем пользователя на страницу корзины
    if existing_address:
        return redirect('cart')
    
    # Иначе, добавляем адрес в черновик
    Manytomany.objects.create(
        address_id_id=address_id,
        meter_id=draft_operation
    )
    
    # Перенаправляем пользователя на страницу корзины
    return redirect('cart') 

def GetCart(request):
    user = request.user
    
    # Получаем количество заявок со статусом "черновик"
    draft_count = Addresses.objects.filter(manytomany__meter_id__meter_status='Черновик').aggregate(count=Count('address_id', distinct=True))['count'] 
    
    # Получаем список всех адресов, которые добавлены в черновик
    draft_addresses = Addresses.objects.filter(manytomany__meter_id__meter_status='Черновик')
    
    return render(request, 'shoppingCart.html', {'data': draft_addresses, 'cart_count': draft_count})

