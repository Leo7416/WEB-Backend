from django.db.models import Q
from django.contrib.auth import authenticate, login, logout  
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema
from water_meter.models import Addresses, WaterMeterReading, Manytomany, CustomUser
from water_meter.serializers import ManyToManySerializer, AddressesSerializer, WaterMeterReadingSerializer, UserSerializer
from water_meter.permissions import IsAdmin, IsManager
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework import status, viewsets
from django.http import HttpResponse, JsonResponse, QueryDict
from django.db import connection
from django.conf import settings
from datetime import datetime
import base64
import redis
import uuid


session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

class UserViewSet(viewsets.ModelViewSet):
    """
    Класс, описывающий методы работы с пользователями
    Осуществляет связь с таблицей пользователей в базе данных
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def register(request):
    """
    Регистрация пользователя
    """
    serializer = UserSerializer(data=request.data)
    print(serializer)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = serializer.save()

    message = {
        'message': 'Пользователь успешно зарегистрировался',
        'user_id': user.id
    }

    return Response(message, status=status.HTTP_201_CREATED)

@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
@authentication_classes([])
def login_view(request):
    """
    Авторизация пользователя
    """
    username = request.data.get("email") 
    password = request.data.get("password")
    user = authenticate(request=request, email=username, password=password)
    if user is not None:
        login(request, user)
        user_id = user.id
        random_key = uuid.uuid4()
        session_storage.set(str(random_key), user_id)
        response_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_admin': user.is_superuser
        }
        response = JsonResponse(response_data)
        response.set_cookie("session_id", random_key, httponly=True, samesite='None', secure=True, path='/')
        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}", status=401)

@api_view(['POST'])
def logout_view(request):
    """
    Выход из профиля
    """
    logout(request)
    return Response({'status': 'Success'})

from django.core.files.base import ContentFile
import os

# ... (ваш существующий код)

@api_view(['GET'])
def get_image_address(request, address_id, format=None):
    """
    Возвращает картинку из услуги
    """
    address = Addresses.objects.get(address_id=address_id)

    if address.images:
        return Response(address.images[2:-1])
    
    return Response({ 'error': 'Поле "image" отсутствует в запросе' })

@api_view(['PUT'])
def update_image_address(request, address_id, format=None):
    """
    Добавляет изображение в услугу
    """
    address = Addresses.objects.get(address_id=address_id)

    if 'images' in request.data:
        image_file = request.data['images']
        image_data = base64.b64encode(image_file.read())
        address.images = image_data
        address.save()

        return Response({'message': 'Изображение успешно добавлено'}, status=status.HTTP_201_CREATED)

    else:
        return Response({'error': 'Поле "images" отсутствует в запросе'}, status=status.HTTP_400_BAD_REQUEST)

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

@swagger_auto_schema(method='post', request_body=AddressesSerializer)
@api_view(['POST'])
@permission_classes([IsAdmin | IsManager])
def post_list_address(request, format=None):    
    """
    Добавляет новую услугу
    """
    data = request.data.copy()

    data['apartment'] = int(data.get('apartment', 0))
    data['meter_reading'] = int(data.get('meter_reading', 0))

    if "images" not in data:
        data['images'] = None  # или любое другое значение по умолчанию, которое вы хотите установить
    else:
        image_file = data['images']
        image_data = base64.b64encode(image_file.read())
        data['images'] = f"{image_data}"
    
    serializer = AddressesSerializer(data=data)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', request_body=AddressesSerializer) 
@api_view(['GET', 'POST'])
def detail_address(request, address_id, format=None):
    address = get_object_or_404(Addresses, address_id=address_id)
    if request.method == 'GET':
        """
        Возвращает информацию об услуге
        """
        address = get_object_or_404(Addresses,address_id=address_id)
        serializer = AddressesSerializer(address)
        return Response(serializer.data)   
    
    elif request.method == 'POST':    
        """
        Добавляет услугу в заявку-черновик
        """
        ssid = request.COOKIES.get("session_id")

        if ssid is not None:
            user_id = session_storage.get(ssid)

            if user_id is not None:
                application = WaterMeterReading.objects.filter(Q(id_user=user_id) & Q(meter_status='Черновик')).first()

                if application is None:
                    application = WaterMeterReading.objects.create(
                    id_user = CustomUser.objects.get(id=user_id),
                    meter_status = 'Черновик',
                    date_creating = datetime.now().strftime("%Y-%m-%d")
                    )
                    application.save()
                    
                new_manytomany, created = Manytomany.objects.get_or_create(
                    meter_id = application,
                    address_id = Addresses.objects.get(address_id=address_id)
                )
                serializer = ManyToManySerializer(new_manytomany)

                if created:
                    new_manytomany.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                
                else:
                    return Response(serializer.data, status=status.HTTP_200_OK)
                
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
@swagger_auto_schema(method='put', request_body=AddressesSerializer)
@api_view(['PUT', 'DELETE'])
@permission_classes([IsAdmin | IsManager])
def update_address(request, address_id, format=None):    

    address = get_object_or_404(Addresses, address_id=address_id)

    if request.method == 'PUT':
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
def get_list_user_application(request, format=None):
    """
    Возвращает список черновой заявки пользователя
    """
    ssid = request.COOKIES.get("session_id")

    if ssid is not None:
        user_id = session_storage.get(ssid)
        
        if user_id is not None:
            
            user = CustomUser.objects.get(id=user_id)
            if WaterMeterReading.objects.filter(id_user=user_id).exists():
                applications = WaterMeterReading.objects.filter(Q(id_user=user_id) & Q(meter_status='Черновик'))
                manytomanys = Manytomany.objects.filter(meter_id__in=applications.values('water_meter_reading_id'))
                data = [
                    {
                    'address_id': manytomany.address_id.address_id,
                    'town': manytomany.address_id.town,
                    'address': manytomany.address_id.address,
                    'apartment': manytomany.address_id.apartment,
                    'house_type': manytomany.address_id.house_type,
                    'meter_reading': manytomany.address_id.meter_reading,
                    'address_status': manytomany.address_id.address_status,
                    'meter_id': manytomany.meter_id.water_meter_reading_id
                }
                    for manytomany in manytomanys
                ]
                return Response(data)
            
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    else:
        return Response(status=status.HTTP_403_FORBIDDEN)

@api_view(['GET'])
def get_list_applications(request, format=None):
    """
    Возвращает список всех заявок
    """
    ssid = request.COOKIES.get("session_id")

    if ssid is not None:
        user_id = session_storage.get(ssid)

        if user_id is not None:
            user = CustomUser.objects.get(id=user_id)

            if user.is_staff or user.is_superuser:
                applications = WaterMeterReading.objects.exclude(Q(meter_status='Черновик') | Q(meter_status='Удалён'))
            else:
                applications = WaterMeterReading.objects.filter(Q(id_user=user_id) & ~Q(meter_status='Черновик') & ~Q(meter_status='Удалена'))

            data = [
                {
                    'water_meter_reading_id': application.water_meter_reading_id,
                    'date_creating': application.date_creating,
                    'date_formation': application.date_formation,
                    'date_completion': application.date_completion,
                    'meter_status': application.meter_status,
                    'username': application.id_user.username
                }
                for application in applications
            ]
            return Response(data)
            
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    else:
        return Response(status=status.HTTP_403_FORBIDDEN)

@api_view(['GET'])
def detail_application(request, water_meter_reading_id, format=None):
    """
    Возвращает информацию о заявке
    """
    ssid = request.COOKIES.get("session_id")

    if ssid is not None:
        user_id = session_storage.get(ssid)

        if user_id is not None:

            applications = WaterMeterReading.objects.filter(Q(id_user=user_id) & ~(Q(status='Черновик') | Q(status='Удалён')))
            application = get_object_or_404(applications, water_meter_reading_id=water_meter_reading_id)
            manytomanys = Manytomany.objects.filter(meter_id=water_meter_reading_id)
            address = []

            for manytomany in manytomanys:
                address.append(Addresses.objects.get(address_id=manytomany.address_id.id))

            serializer_meter = WaterMeterReadingSerializer(application)
            serializer_address = AddressesSerializer(address, many=True)
            response_data = {'Заявка': serializer_meter.data, 'Услуги': serializer_address.data}

            return Response(response_data)
        
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    else:
        return Response(status=status.HTTP_403_FORBIDDEN)
    
@api_view(['DELETE'])
def delete_application(request, water_meter_reading_id, format=None):    
    """
    Удаляет информацию о заявке
    """
    ssid = request.COOKIES.get("session_id")

    if ssid is not None:
        user_id = session_storage.get(ssid)

        if user_id is not None:

            applications = WaterMeterReading.objects.filter(Q(id_user=user_id) & Q(status='Черновик'))
            application = get_object_or_404(applications, water_meter_reading_id=water_meter_reading_id)
            application.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    else:
        return Response(status=status.HTTP_403_FORBIDDEN)


@swagger_auto_schema(method='put', request_body=WaterMeterReadingSerializer)
@api_view(['PUT'])
def put_status_user_application(request, water_meter_reading_id, format=None):
    """
    Формирование заявки создателем
    """
    ssid = request.COOKIES.get("session_id")

    if ssid is not None:
        user_id = session_storage.get(ssid)

        if user_id is not None:

            applications = WaterMeterReading.objects.filter(Q(id_user=user_id) & Q(meter_status='Черновик'))
            application = get_object_or_404(applications, water_meter_reading_id=water_meter_reading_id)
            application.meter_status = 'Сформирована'
            application.date_formation = datetime.now().strftime("%Y-%m-%d")
            application.save()
            serializer = WaterMeterReadingSerializer(application)
            return Response(serializer.data)
            
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    else:
        return Response(status=status.HTTP_403_FORBIDDEN)


@swagger_auto_schema(method='put', request_body=WaterMeterReadingSerializer)
@api_view(['PUT'])
@permission_classes([IsAdmin | IsManager])
def put_status_moderator_application(request, water_meter_reading_id, format=None):
    """
    Одобрение или отклонение заявки модератором
    """
    ssid = request.COOKIES.get("session_id")
    if ssid is not None:
        user_id = session_storage.get(ssid)

        if user_id is not None:
            user = CustomUser.objects.get(id=user_id)
            meter_reading = get_object_or_404(WaterMeterReading, water_meter_reading_id=water_meter_reading_id)

            if meter_reading.meter_status == 'Сформирована':
                serializer = WaterMeterReadingSerializer(meter_reading, data=request.data)
                new_status = request.data.get('meter_status')

                if new_status in ('Одобрена', 'Отклонена'):
                    meter_reading.date_completion = datetime.now().strftime("%Y-%m-%d")
                    meter_reading.moderator = user.username
                    meter_reading.meter_status = new_status
                    meter_reading.save()
                    serializer = WaterMeterReadingSerializer(meter_reading)
                    return Response(serializer.data)
                    
                else:
                    error_message = "Неправильный статус. Допустимые значения: 'Одобрена', 'Отклонена'."
                    return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)
                
            else:
                error_message = "Нельзя сменить статус у этой заявки."
                return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)
            
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    else:
        return Response(status=status.HTTP_403_FORBIDDEN)


@swagger_auto_schema(method='put', request_body=WaterMeterReadingSerializer)
@permission_classes([AllowAny])
@api_view(['PUT'])
def put_async_application(request, format=None):
    """
    Обновление поля асинхронным сервером
    """ 
    const_token = 'access_token'
    if const_token != request.data.get('token'):
        return Response({'message': 'Ошибка, токен не соответствует'}, status=status.HTTP_403_FORBIDDEN)
    
    meter_id = request.data.get('meter_id')
    address_id = request.data.get('address_id')
    manytomany = Manytomany.objects.get(meter_id=meter_id, address_id=address_id)
    manytomany.price = request.data.get('price')
    manytomany.save()

    serializer = ManyToManySerializer(manytomany)
    return Response(serializer.data)

@api_view(['DELETE'])
def delete_address_from_applications(request, address_id, format=None):  
    """
    Удаляет услугу из заявки
    """
    ssid = request.COOKIES.get("session_id")
    print(ssid)
    if ssid is not None:
        user_id = session_storage.get(ssid)

        if user_id is not None:

            manytomanys = Manytomany.objects.filter(meter_id__id_user=user_id, meter_id__meter_status='Черновик')
            manytomany = get_object_or_404(manytomanys, address_id=address_id)  
            manytomany.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)
        
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    else:
        return Response(status=status.HTTP_403_FORBIDDEN)
    
