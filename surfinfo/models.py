from django.db import models
from datetime import datetime


# Create your models here.
class TestModel(models.Model):
    name = models.CharField(max_length=50)
    number = models.DecimalField(max_digits=4, decimal_places=2)
    timestamp = models.DateTimeField()

    def __str__(self):
        return str(self.name) + ': ' + str(self.timestamp) + ', ' + str(self.number)


class Swell(models.Model):
    height = models.DecimalField(max_digits=4, decimal_places=2)
    period = models.DecimalField(max_digits=4, decimal_places=2)
    direction = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return 'height: ' + str(self.height) + ', period: ' + str(self.period) + ', direction: ' + str(self.direction)


class Tide(models.Model):
    timestamp = models.DateTimeField()
    height = models.DecimalField(max_digits=4, decimal_places=2)
    type = models.CharField(max_length=20)

    def __str__(self):
        return str(self.timestamp) + ': ' + str(self.height) + ' ft, ' + self.type

class SurfSpot(models.Model):
    surflineId = models.CharField(max_length=100)
    spotName = models.CharField(max_length=100)

class SurfSession(models.Model):
    spotName = models.CharField(max_length=100)
    surflineId = models.CharField(max_length=100)

    timeIn = models.DateTimeField()
    timeOut = models.DateTimeField()

    waveCount = models.IntegerField()
    surfScore = models.IntegerField()
    crowdScore = models.CharField(max_length=20)

    # tides throughout a surf session
    tides = models.ManyToManyField(Tide)

    # swells at the start of a surf session
    swells = models.ManyToManyField(Swell)

    board = models.CharField(max_length=100)

    def __str__(self):
        #    print('**swells**')
        #    for timeBlock in surfReport['data']['wave']:
        #        #    print('timestamp: ' + str(timeBlock['timestamp']))
        #        print(datetime.fromtimestamp(timeBlock['timestamp']))
        #
        #        for each in timeBlock['swells']:
        #            if each['height'] != 0:
        #                print(each)
        #        print()

        #    print('**tides**')
        #    for timeBlock in tideReport['data']['tides']:
        #        print(datetime.fromtimestamp(timeBlock['timestamp']))
        #        print(timeBlock['height'])
        #        if timeBlock['type'] != 'NORMAL':
        #            print(timeBlock['type'])
        #        print()
        return str(self.spotName) + ': ' + str(self.waveCount) + ' waves'
