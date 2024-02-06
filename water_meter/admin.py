from django.contrib import admin
from .models import CustomUser
from .models import WaterMeterReading
from .models import Addresses

admin.site.register(CustomUser)
admin.site.register(WaterMeterReading)
admin.site.register(Addresses)