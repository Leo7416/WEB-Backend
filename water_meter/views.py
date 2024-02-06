from django.db.models import Q
from django.shortcuts import render
from water_meter.models import Addresses
from water_meter.models import WaterMeterReading
from django.db import connection


def GetApplications(request):
    data = Addresses.objects.filter(address_status='Действует')
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
    data = Addresses.objects.filter(address_status='Действует')
    # SQL-запрос для изменения статуса записи
    sql = "UPDATE addresses SET address_status = 'Удален' WHERE address_id = %s;"
    
    # Выполняем SQL-запрос
    with connection.cursor() as cursor:
        cursor.execute(sql, [address_id])
    
    return render(request, 'applications.html', {'data': data})  