from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader

from .models import Swell, Tide, SurfSession
import requests
import json
from datetime import datetime, timedelta, date
from django.utils.timezone import make_aware

from .forms import AddSessionForm

def index(request):
    # if this is a POST request, process form data
    if request.method == 'POST':
        form = AddSessionForm(request.POST)

        if form.is_valid():
            # process the data
            today = datetime.date
            startDateTime = datetime.combine(date.today(), form.cleaned_data['startTime'])
            endDateTime = datetime.combine(date.today(), form.cleaned_data['endTime'])
            print(startDateTime)
            print(endDateTime)
            print(form.cleaned_data['surfScore'])
            print(form.cleaned_data['crowdScore'])

            # redirect to a new URL
            return HttpResponseRedirect('addsession')

    # if this is not a POST request, create the form
    else:
        form = AddSessionForm()

    return render(request, 'surfinfo/sessionform.html', {'form': form, 'today': datetime.now()})

def addsession(request):
    surf = requests.get(
        'https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=5842041f4e65fad6a7708807&days=1&intervalHours=1&maxHeights=false')
    surfReport = json.loads(surf.text)

    tides = requests.get(
        'https://services.surfline.com/kbyg/spots/forecasts/tides?spotId=5842041f4e65fad6a7708807&days=1')
    tideReport = json.loads(tides.text)

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
        todaySession = SurfSession(spotName='Pleasure Point, Santa Cruz',
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
                print(swell)
                swell.save()
                todaySession.swells.add(swell)

        # extract tide info for every hour in a session
        #   this clumsy structure is intended to grab hourly tides for a session, PLUS "special" tides
        #   like high tide, low tide, etc
        #   it is also intended to grab at least one tide entry, even if session was super short
        for each in tideReport['data']['tides']:
            if each['timestamp'] > startTime.timestamp():
                tide = Tide(timestamp=datetime.fromtimestamp(each['timestamp']), height=each['height'], type=each['type'])
                print(tide)
                tide.save()
                todaySession.tides.add(tide)

            # if timestamp of this tide "block" is later than session end time, break out of for loop
            if each['timestamp'] > endTime.timestamp():
                break


    print('**session**')
    print(todaySession)

    return render(request, 'surfinfo/addsession.html', {'surfsession': todaySession})
