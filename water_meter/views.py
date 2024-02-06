from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from water_meter.models import Addresses, WaterMeterReading, Manytomany
from water_meter.serializers import ManyToManySerializer, AddressesSerializer, WaterMeterReadingSerializer
from django.db import connection
from rest_framework.response import Response
from rest_framework.decorators import api_view
import base64
from rest_framework import status

def GetApplications(request):
    data = Addresses.objects.filter(address_status='Действует')
    for address in data:
        if address.images:
            address.images = base64.b64encode(address.images).decode()
    return render(request, 'applications.html', {'data': data})

def GetApplication(request, address_id):
    address = Addresses.objects.get(address_id=address_id)
    meter_reading = address.meter_reading
    address.images = base64.b64encode(address.images).decode()
    return render(request, 'application.html', {'application': address, 'application_reading': meter_reading})

        
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

    data = Addresses.objects.filter(address_status='Действует')
    for address in data:
        if address.images:
            address.images = base64.b64encode(address.images).decode()
    
    return render(request, 'applications.html', {'data': data})  

@api_view(['Get'])
def get_search_addresses(request, format=None): 
    """
    Возвращает список услуг по запросу
    """
    query = request.GET.get('query', '')
    
    if query.strip() == '':
        # Если запрос пустой, вернуть все адреса
        all_addresses = Addresses.objects.all()
        serializer = AddressesSerializer(all_addresses, many=True)
        return Response(serializer.data)

    if query.isnumeric():
        filtered_addresses = Addresses.objects.filter(address=query)
    else:
        filtered_addresses = Addresses.objects.filter(
            Q(town=query) |
            Q(address=query)
        )

    
    serializer = AddressesSerializer(filtered_addresses, many=True)
    return Response(serializer.data)


@api_view(['Get'])
def get_list_addresses(request, format=None):
    """
    Возвращает список услуг
    """
    addresses = Addresses.objects.all()
    serializer = AddressesSerializer(addresses, many=True)
    return Response(serializer.data)


@api_view(['Get', 'Post', 'Put', 'Delete'])
def detail_address(request, address_id, format=None):
    address = get_object_or_404(Addresses, address_id=address_id)
    if request.method == 'GET':
        """
        Возвращает информацию об услуге
        """
        serializer = AddressesSerializer(address)
        return Response(serializer.data)   
    
    elif request.method == 'POST':    
        """
        Добавляет услугу в последнюю заявку
        """
        new_manytomany, created = Manytomany.objects.get_or_create(
            id_application = WaterMeterReading.objects.latest('water_meter_reading_id'),
            id_address = Addresses.objects.get(address_id=address_id)
        )
        serializer = ManyToManySerializer(new_manytomany)
        if created:
            new_manytomany.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        """
        Обновляет информацию об услуге
        """
        serializer = AddressesSerializer(address, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':    
        """
        Удаляет информацию об услуге
        """
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def get_image_address(request, address_id, format=None):
    """
    Возвращает картинку из услуги
    """
    address = Addresses.objects.get(address_id=address_id)
    if address.images:
        address.images = base64.b64encode(address.images).decode()
    return Response(address.images, content_type="image/jpeg")


@api_view(['Post'])
def post_list_address(request, format=None):    
    """
    Добавляет новую услугу
    """
    serializer = AddressesSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['Get'])
def get_list_applications(request, format=None):
    """
    Возвращает список заявок
    """
    applications = WaterMeterReading.objects.all()
    serializer = WaterMeterReadingSerializer(applications, many=True)
    return Response(serializer.data)


@api_view(['Get', 'Delete'])
def detail_application(request, water_application_reading_id, format=None):
    application = get_object_or_404(WaterMeterReading, water_application_reading_id=water_application_reading_id)
    if request.method == 'GET':
        """
        Возвращает информацию о заявке
        """
        serializer = WaterMeterReadingSerializer(application)
        return Response(serializer.data)
    elif request.method == 'DELETE':    
        """
        Удаляет информацию о заявке
        """
        application.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['Put'])
def put_status_user_application(request, water_meter_reading_id, format=None):
    """
    Обновляет информацию о статусе создателя
    """
    application = get_object_or_404(WaterMeterReading, water_application_reading_id=water_meter_reading_id)
    application.meter_status = 'Удалён'
    serializer = WaterMeterReadingSerializer(application, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['Put'])
def put_status_moderator_application(request, water_meter_reading_id, format=None):
    """
    Обновляет информацию о статусе модератора
    """
    application = get_object_or_404(WaterMeterReading, water_meter_reading_id=water_meter_reading_id)
    serializer = WaterMeterReadingSerializer(application, data=request.data)
    new_status = request.data.get('meter_status')
    if new_status != 'Удалён':
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({'error': "Нельзя изменить статус на 'Удалён'."}, status=status.HTTP_403_FORBIDDEN)


@api_view(['Delete'])
def delete_address_from_applications(request, id, format=None):    
    """
    Удаляет услугу из заявки
    """
    manytomany = get_object_or_404(Manytomany, id=id)
    manytomany.delete()
    manytomanys = Manytomany.objects.all()
    serializer = ManyToManySerializer(manytomanys, many=True)
    return Response(serializer.data)