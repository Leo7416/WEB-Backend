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
def add_image_address(request, address_id, format=None):
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
        data['images'] = "b'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'"
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
    
