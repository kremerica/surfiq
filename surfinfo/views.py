from django.http import HttpResponse
from .models import TestModel
from .models import Swell, Tide, SurfSession
import requests
import json
from datetime import datetime
from django.utils.timezone import make_aware


def index(request):
    surf = requests.get(
        'https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=5842041f4e65fad6a7708807&days=1&intervalHours=3&maxHeights=false')
    surfReport = json.loads(surf.text)

    tides = requests.get(
        'https://services.surfline.com/kbyg/spots/forecasts/tides?spotId=5842041f4e65fad6a7708807&days=1')
    tideReport = json.loads(tides.text)

    print('**swells**')
    for timeBlock in surfReport['data']['wave']:
        #    print('timestamp: ' + str(timeBlock['timestamp']))
        print(datetime.fromtimestamp(timeBlock['timestamp']))

        for each in timeBlock['swells']:
            if each['height'] != 0:
                print(each)
        print()

    print('**tides**')
    for timeBlock in tideReport['data']['tides']:
        print(datetime.fromtimestamp(timeBlock['timestamp']))
        print(timeBlock['height'])
        if timeBlock['type'] != 'NORMAL':
            print(timeBlock['type'])
        print()


    # create a SurfSession object for an arbitrary hour for TODAY's surf conditions
    # create and save the base SurfSession object
    testSession = SurfSession(spotName='test spot',
                              surflineId='5842041f4e65fad6a7708807',
                              timeIn=datetime.now(),
                              timeOut=datetime.now(),
                              waveCount=10,
                              surfScore=5,
                              crowdScore=5,
                              board='UNTITLED 5\'11')
    print('**session**')
    print(testSession)

    # create + save + add each Swell


    # create + save + add each Tide

    # using the TestModel to extract a query string param and save it to DB
    test = TestModel(name=request.GET['name'], number=2.2, timestamp=make_aware(datetime.now()))
    test.save()

    # print all TestModel objects to validate that model.save() worked as expected
    print(TestModel.objects.all())

    # return name of current TestModel object to validate query string parameter was read correctly
    return HttpResponse('Hi ' + test.name)