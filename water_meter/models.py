from django.db import models


class Addresses(models.Model):
    address_id = models.AutoField(primary_key=True)
    town = models.CharField(max_length=60)
    address = models.CharField(max_length=50)
    apartment = models.IntegerField()
    house_type = models.CharField(max_length=12)
    meter_reading = models.IntegerField()
    images = models.BinaryField()
    address_status = models.CharField(max_length=12)
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'addresses'


class Manytomany(models.Model):
    address = models.OneToOneField(Addresses, models.DO_NOTHING, primary_key=True)  # The composite primary key (address_id, water_meter_reading_id) found, that is not supported. The first column is selected.
    water_meter_reading = models.ForeignKey('Watermeterreading', models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'manytomany'
        unique_together = (('address', 'water_meter_reading'),)


class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    second_name = models.CharField(max_length=50)
    age = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'users'


class WaterMeterReading(models.Model):
    water_meter_reading_id = models.AutoField(primary_key=True)
    create_date = models.DateField()
    fixation_date = models.DateField()
    finish_date = models.DateField()
    full_name_creater = models.CharField(max_length=50)
    meter_status = models.CharField(max_length=20)

    class Meta:
        managed = True
        db_table = 'watermeterreading'