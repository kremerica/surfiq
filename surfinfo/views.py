from django.http import HttpResponse
from .models import TestModel
from .models import Swell, Tide, SurfSession
import requests
import json
from datetime import datetime, timedelta
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

    # assign an arbitrary session end time N hours after start time
    endTime = startTime + timedelta(hours=2)

    # grab timestamp from first swell
    swellTime = datetime.fromtimestamp(surfReport['data']['wave'][0]['timestamp'])

    # confirm same date between swell and session start time
    if (startTime.date() == swellTime.date()):
        # create a SurfSession object for an arbitrary hour for TODAY's surf conditions
        # create and save the base SurfSession object
        todaySession = SurfSession(spotName='test spot',
                                  surflineId='5842041f4e65fad6a7708807',
                                  timeIn=startTime,
                                  timeOut=endTime,
                                  waveCount=10,
                                  surfScore=5,
                                  crowdScore=5,
                                  board='UNTITLED 5\'11')
        # save to DB
        todaySession.save()


        # find the "hour index" that maps to the same hour as the start of the session
        startHourIndex = startTime.hour

        # extract all swells for that hour
        for each in surfReport['data']['wave'][startHourIndex]['swells']:
            # plop all non-zero-height swells into Swell objects, save to DB, add to surf session
            if each['height'] != 0:
                swell = Swell(height=each['height'], period=each['period'], direction=each['direction'])
                swell.save()
                todaySession.swells.add(swell)

        # extract tide info for every hour in a session
        #   this clumsy structure is intended to grab hourly tides for a session, PLUS "special" tides
        #   like high tide, low tide, etc
        #   it is also intended to grab at least one tide entry, even if session was super short
        for each in tideReport['data']['tides']:
            if each['timestamp'] > startTime.timestamp():
                tide = Tide(timestamp=datetime.fromtimestamp(each['timestamp']), height=each['height'], type=each['type'])
                tide.save()
                todaySession.tides.add(tide)

            # if timestamp of this tide "block" is later than session end time, break out of for loop
            if each['timestamp'] > endTime.timestamp():
                break


    print('**session**')
    print(todaySession)


    # using the TestModel to extract a query string param and save it to DB
    test = TestModel(name=request.GET['name'], number=2.2, timestamp=make_aware(datetime.now()))
    test.save()

    # print all TestModel objects to validate that model.save() worked as expected
#    print(TestModel.objects.all())

    # return name of current TestModel object to validate query string parameter was read correctly
    return HttpResponse('Hi ' + test.name)