from django.http import HttpResponse
from .models import TestModel
from .models import Swell, Tide, SurfSession
import requests
import json
from datetime import datetime
from django.utils.timezone import make_aware


def index(request):
    surf = requests.get(
        'https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=5842041f4e65fad6a7708807&days=1&intervalHours=1&maxHeights=false')
    surfReport = json.loads(surf.text)

    tides = requests.get(
        'https://services.surfline.com/kbyg/spots/forecasts/tides?spotId=5842041f4e65fad6a7708807&days=1')
    tideReport = json.loads(tides.text)

#    print('**swells**')
#    for timeBlock in surfReport['data']['wave']:
#        #    print('timestamp: ' + str(timeBlock['timestamp']))
#        print(datetime.fromtimestamp(timeBlock['timestamp']))

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

# extract session start and end time (hour of day)
    # assign arbitrary session start time
    startTime = datetime.now()

    # grab timestamp from first swell
    swellTime = datetime.fromtimestamp(surfReport['data']['wave'][0]['timestamp'])

    # confirm same date between swell and session start time
    if (startTime.date() == swellTime.date()):
        # create a SurfSession object for an arbitrary hour for TODAY's surf conditions
        # create and save the base SurfSession object
        todaySession = SurfSession(spotName='test spot',
                                  surflineId='5842041f4e65fad6a7708807',
                                  timeIn=datetime.now(),
                                  timeOut=datetime.now(),
                                  waveCount=10,
                                  surfScore=5,
                                  crowdScore=5,
                                  board='UNTITLED 5\'11')
        # save to DB
        todaySession.save()


        # find the "hour index" that maps to the same hour as the start of the session
        hourIndex = startTime.hour

        # extract all swells for that hour
        for each in surfReport['data']['wave'][hourIndex]['swells']:
            # plop all non-zero-height swells into Swell objects, save to DB, add to surf session
            if each['height'] != 0:
                swell = Swell(height=each['height'], period=each['period'], direction=each['direction'])
                swell.save()
                todaySession.swells.add(swell)

    # get swell info for session start time

    # get tide info for every hour in a session

    # add swell and tide info to surf session

    # add surf session to DB

    print('**session**')
    print(todaySession)

    # create + save + add each Swell


    # create + save + add each Tide

    # using the TestModel to extract a query string param and save it to DB
    test = TestModel(name=request.GET['name'], number=2.2, timestamp=make_aware(datetime.now()))
    test.save()

    # print all TestModel objects to validate that model.save() worked as expected
    print(TestModel.objects.all())

    # return name of current TestModel object to validate query string parameter was read correctly
    return HttpResponse('Hi ' + test.name)