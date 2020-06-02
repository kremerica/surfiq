from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader

from .models import Swell, Tide, SurfSession
import requests
import json
from datetime import datetime, timedelta, date, timezone
import django.utils.timezone

from .forms import AddSessionForm

def index(request):
    # if this is a POST request, process form data
    if request.method == 'POST':
        form = AddSessionForm(request.POST)

        if form.is_valid():
            # process the data
            # grab swell info from Surfline API (do this first to get the surf spot UTC offset)
            surf = requests.get(
                'https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=5842041f4e65fad6a7708807&days=1&intervalHours=1&maxHeights=false')
            surfReport = json.loads(surf.text)

            # grab tide info from Surfline API
            tides = requests.get(
                'https://services.surfline.com/kbyg/spots/forecasts/tides?spotId=5842041f4e65fad6a7708807&days=1')
            tideReport = json.loads(tides.text)

            # get the UTC offset from the surf report, use as timezone in surf session
            surfUtcOffset = timezone(offset=timedelta(hours=surfReport['associated']['utcOffset']))

            # get the UTC offset from the tide report for sanity check
            tideUtcOffset = timezone(offset=timedelta(hours=tideReport['associated']['utcOffset']))

            # check sanity
            if surfUtcOffset != tideUtcOffset:
                print("MISMATCH BETWEEN SURF REPORT TIMEZONE AND TIDE REPORT TIMEZONE")

            # convert start and end times to datetimes with today's date
            startDateTime = datetime.combine(date.today(), form.cleaned_data['startTime'], tzinfo=surfUtcOffset)
            endDateTime = datetime.combine(date.today(), form.cleaned_data['endTime'], tzinfo=surfUtcOffset)

            # create a SurfSession object for an arbitrary hour for TODAY's surf conditions
            # create and save the base SurfSession object
            todaySession = SurfSession(spotName='Pleasure Point, Santa Cruz',
                                       surflineId='5842041f4e65fad6a7708807',
                                       spotUtcOffset=surfReport['associated']['utcOffset'],
                                       timeIn=startDateTime,
                                       timeOut=endDateTime,
                                       waveCount=form.cleaned_data['waveCount'],
                                       surfScore=form.cleaned_data['surfScore'],
                                       crowdScore=form.cleaned_data['crowdScore'],
                                       board='UNTITLED 5\'11')
            # save to DB
            todaySession.save()

            # find the "hour index" that maps to the same hour as the start of the session
            startHourIndex = startDateTime.hour

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
                if each['timestamp'] > startDateTime.timestamp():
                    tide = Tide(timestamp=datetime.fromtimestamp(each['timestamp'], tz=surfUtcOffset), height=each['height'],
                                type=each['type'])
                    tide.save()
                    todaySession.tides.add(tide)

                # if timestamp of this tide "block" is later than session end time, break out of for loop
                if each['timestamp'] > endDateTime.timestamp():
                    break

            # redirect to a new URL
            return HttpResponseRedirect('congratsbro?sessionid=' + str(todaySession.id))

    # if this is not a POST request, create the form
    else:
        form = AddSessionForm()

    return render(request, 'surfinfo/sessionform.html', {'form': form, 'today': datetime.now()})

def congratsbro(request):
    if request.GET['sessionid']:
        if SurfSession.objects.filter(id=request.GET['sessionid']).exists():
            todaySession = SurfSession.objects.get(id=request.GET['sessionid'])
        else:
            todaySession = None
    else:
        todaySession = None

    # not for future: might need better conversion than typecasting as int for surfsession.spotUtcOffset from decimal to hours + minutes
    return render(request, 'surfinfo/addsession.html', {'surfsession': todaySession, 'surftimezone': timezone(offset=timedelta(hours=int(todaySession.spotUtcOffset)))})
