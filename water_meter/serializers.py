from water_meter.models import Manytomany, Addresses, WaterMeterReading
from rest_framework import serializers
from collections import OrderedDict


class ManyToManySerializer(serializers.ModelSerializer):
    class Meta:
        model = Manytomany
        fields = '__all__'


class AddressesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Addresses
        fields = '__all__'


class WaterMeterReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterMeterReading
        fields = '__all__'
