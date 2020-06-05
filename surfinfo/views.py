from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader

from .models import Swell, Tide, SurfSession
import requests
import json
from datetime import datetime, timedelta, date, timezone
import django.utils.timezone

from .forms import AddSessionForm, AddSurfSpot

def index(request):
    # if this is a POST request, process form data
    if request.method == 'POST':
        form = AddSessionForm(request.POST)

        if form.is_valid():
            # process the data
            # grab swell info from Surfline API (do this first to get the surf spot UTC offset)
            surfSpotId = form.cleaned_data['surfSpot'].split(':')[1]
            surfSpotName = form.cleaned_data['surfSpot'].split(':')[0]

            # only process the data if there was a spot selected
            if surfSpotId != 'NONE':
                surfUrl = 'https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=' + surfSpotId + '&days=1&intervalHours=1&maxHeights=false'
                surf = requests.get(surfUrl)
                surfReport = json.loads(surf.text)

                # grab tide info from Surfline API
                tideUrl = 'https://services.surfline.com/kbyg/spots/forecasts/tides?spotId=' + surfSpotId + '&days=1'
                tides = requests.get(tideUrl)
                tideReport = json.loads(tides.text)

                # print('SURF URL: ' + surfUrl)
                # print('TIDE URL: ' + tideUrl)

                # get the UTC offset from the surf report, use as timezone in surf session
                surfUtcOffset = timezone(offset=timedelta(hours=surfReport['associated']['utcOffset']))

                # get the UTC offset from the tide report for sanity check
                tideUtcOffset = timezone(offset=timedelta(hours=tideReport['associated']['utcOffset']))

                # check sanity
                if surfUtcOffset != tideUtcOffset:
                    print("MISMATCH BETWEEN SURF REPORT TIMEZONE AND TIDE REPORT TIMEZONE")

                # convert start and end times to datetimes with today's date
                startDateTime = datetime.combine(datetime.now(tz=surfUtcOffset).date(), form.cleaned_data['startTime'], tzinfo=surfUtcOffset)
                endDateTime = datetime.combine(datetime.now(tz=surfUtcOffset).date(), form.cleaned_data['endTime'], tzinfo=surfUtcOffset)

                # print("SESSION START DATETIME: " + str(startDateTime))
                # print("SESSION END DATETIME: " + str(endDateTime))

                # create a SurfSession object for an arbitrary hour for TODAY's surf conditions
                # create and save the base SurfSession object
                todaySession = SurfSession(spotName=surfSpotName,
                                           surflineId=surfSpotId,
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
                    # package tide datetime into object for comparison
                    tideDateTime = datetime.fromtimestamp(each['timestamp'], tz=surfUtcOffset)
                #    print("TIDE DATETIME: " + str(tideDateTime))

                    if tideDateTime >= startDateTime:
                        tide = Tide(timestamp=tideDateTime, height=each['height'], type=each['type'])
                        tide.save()
                        todaySession.tides.add(tide)

                    # if timestamp of this tide "block" is later than session end time, break out of for loop
                    if tideDateTime > endDateTime:
                        break

                # redirect to a new URL
                return HttpResponseRedirect('congratsbro?sessionid=' + str(todaySession.id))
            else:
                return HttpResponseRedirect('newspotbro')

    # if this is not a POST request, create the form
    else:
        form = AddSessionForm()

    return render(request, 'surfinfo/sessionform.html', {'form': form})

def congratsbro(request):
    if request.GET['sessionid']:
        if SurfSession.objects.filter(id=request.GET['sessionid']).exists():
            todaySession = SurfSession.objects.get(id=request.GET['sessionid'])
        else:
            todaySession = None
    else:
        todaySession = None

    # note for future: might need better conversion than typecasting as int for surfsession.spotUtcOffset from decimal to hours + minutes
    return render(request, 'surfinfo/addsession.html', {'surfsession': todaySession, 'surftimezone': timezone(offset=timedelta(hours=int(todaySession.spotUtcOffset)))})

def newspotbro(request):
    # if this is a POST request, process form data
    if request.method == 'POST':
        form = AddSurfSpot(request.POST)

        if form.is_valid():
            # process the data
            print(form.cleaned_data['spotName'])

            # redirect to a thank you URL
            return HttpResponseRedirect('thanksbro?spotname=' + form.cleaned_data['spotName'])
    # if this is not a POST request, create the form
    else:
        form = AddSurfSpot()

    return render(request, 'surfinfo/addsurfspot.html', {'form': form})

def thanksbro(request):
    if request.GET['spotname']:
        spotName = request.GET['spotname'];
    else:
        spotName = None

    return render(request, 'surfinfo/spotthankyou.html', {'spotName': spotName})