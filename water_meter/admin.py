from django.contrib import admin
from .models import Users
from .models import WaterMeterReading
from .models import Addresses

admin.site.register(Users)
admin.site.register(WaterMeterReading)
admin.site.register(Addresses)