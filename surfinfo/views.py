from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db.models import Avg, Count, Sum

from .models import Swell, Tide, SurfSession, SurfSpot
import requests
import json
from datetime import datetime, timedelta, date, timezone
import django.utils.timezone

from .forms import AddSessionForm, AddSurfSpot, GetMatchingSessions


# adding a session
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

                # get the UTC offset from the surf report, use as timezone in surf session
                surfUtcOffset = timezone(offset=timedelta(hours=surfReport['associated']['utcOffset']))

                # get the UTC offset from the tide report for sanity check
                tideUtcOffset = timezone(offset=timedelta(hours=tideReport['associated']['utcOffset']))

                # check sanity
                if surfUtcOffset != tideUtcOffset:
                    print("MISMATCH BETWEEN SURF REPORT TIMEZONE AND TIDE REPORT TIMEZONE")

                # convert start and end times to datetimes with today's date
                startDateTime = datetime.combine(datetime.now(tz=surfUtcOffset).date(), form.cleaned_data['startTime'],
                                                 tzinfo=surfUtcOffset)
                endDateTime = datetime.combine(datetime.now(tz=surfUtcOffset).date(), form.cleaned_data['endTime'],
                                               tzinfo=surfUtcOffset)

                # create a SurfSession object for an arbitrary hour for TODAY's surf conditions
                # create and save the base SurfSession object
                todaySession = SurfSession(spotName=surfSpotName,
                                           surflineId=surfSpotId,
                                           spotUtcOffset=surfReport['associated']['utcOffset'],
                                           timeIn=startDateTime,
                                           timeOut=endDateTime,
                                           waveCount=-1,
                                           surfScore=form.cleaned_data['surfScore'],
                                           crowdScore=form.cleaned_data['crowdScore'],
                                           board='NONE')
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

                    if tideDateTime.hour >= startDateTime.hour and endDateTime > tideDateTime:
                        tide = Tide(timestamp=tideDateTime, height=each['height'], type=each['type'])
                        tide.save()
                        todaySession.tides.add(tide)

                # redirect to a new URL
                return HttpResponseRedirect('congratsbro?sessionid=' + str(todaySession.id))
            else:
                return HttpResponseRedirect('newspotbro')

    # if this is not a POST request, create the form
    else:
        form = AddSessionForm()

    return render(request, 'surfinfo/sessionform.html', {'form': form})


# thank you for adding a session
def sessionthankyou(request):
    if request.GET['sessionid']:
        if SurfSession.objects.filter(id=request.GET['sessionid']).exists():
            todaySession = SurfSession.objects.get(id=request.GET['sessionid'])
        else:
            todaySession = None
    else:
        todaySession = None

    # note for future: might need better conversion than typecasting as int for surfsession.spotUtcOffset from decimal to hours + minutes
    return render(request, 'surfinfo/sessionthankyou.html', {'surfsession': todaySession, 'surftimezone': timezone(
        offset=timedelta(hours=int(todaySession.spotUtcOffset)))})


# request a new surf spot
def requestnewspot(request):
    # if this is a POST request, process form data
    if request.method == 'POST':
        form = AddSurfSpot(request.POST)

        if form.is_valid():
            # process the data
            newSpot = SurfSpot(spotName=form.cleaned_data['spotName'], surflineId="TBD")
            newSpot.save()

            # redirect to a thank you URL
            return HttpResponseRedirect('thanksbro?spotid=' + str(newSpot.id))
    # if this is not a POST request, create the form
    else:
        form = AddSurfSpot()

    return render(request, 'surfinfo/surfspotform.html', {'form': form})


# thank the user for requesting a new surf spot
def spotthankyou(request):
    spotid = request.GET.get('spotid')

    if spotid:
        if SurfSpot.objects.filter(id=request.GET['spotid']).exists():
            newSpot = SurfSpot.objects.get(id=request.GET['spotid'])
        else:
            newSpot = None
    else:
        newSpot = None

    return render(request, 'surfinfo/spotthankyou.html', {'newSpot': newSpot})


# find matching sessions for surf conditions
def historicalmatches(request):
    form = GetMatchingSessions()

    # self-redirect with query string params
    if form.is_valid():
        # process the data
        height = form.cleaned_data['swellHeight']
        period = form.cleaned_data['swellPeriod']
        direction = form.cleaned_data['swellDirection']
        tide = form.cleaned_data['tideHeight']

        # redirect to a thank you URL
        return HttpResponseRedirect('whereto?height=' + str(height) +
                                    '&period=' + str(period) +
                                    '&direction=' + str(direction) +
                                    '&tide=' + str(tide))


    height = float(request.GET.get('swellHeight', 0))
    period = float(request.GET.get('swellPeriod', 0))
    direction = float(request.GET.get('swellDirection', 0))
    tide = float(request.GET.get('tideHeight', 0))

    HEIGHT_FACTOR = 0.2
    PERIOD_FACTOR = 0.2
    DIRECTION_FACTOR = 12
    TIDE_FACTOR = 1

    # get a queryset of all sessions
    rawSessions = SurfSession.objects.filter(swells__height__gte=height*(1-HEIGHT_FACTOR),
                                          swells__height__lte=height*(1+HEIGHT_FACTOR),
                                          swells__period__gte=period*(1-PERIOD_FACTOR),
                                          swells__period__lte=period*(1+PERIOD_FACTOR),
                                          swells__direction__gte=direction-DIRECTION_FACTOR,
                                          swells__direction__lte=direction+DIRECTION_FACTOR,
                                          tides__height__gte=tide-TIDE_FACTOR,
                                          tides__height__lte=tide+TIDE_FACTOR).distinct()

    print()
    print("*** CONDITIONS ***")
    print("*** " + str(height) + "ft " + str(period) + "s at " + str(direction) + "°, tide height " + str(tide))
    print("*** PREVIOUS SURFS ***")

    sessions = rawSessions.values("spotName").annotate(Avg("surfScore"), Avg("waveCount"), Count("id")).order_by('-surfScore__avg')

    if sessions.exists():
        for each in sessions:
            print(str(each["spotName"]) + ": " +
                  str(each["id__count"]) + " sessions, avg score " +
                  str(round(each["surfScore__avg"], 1)) + "/5, avg wave count " +
                  str(round(each["waveCount__avg"], 1)))

    print()

    return render(request, 'surfinfo/getmatchingsessions.html',
                  {'form': form,
                   'swellHeight': height,
                   'swellPeriod': period,
                   'swellDirection': direction,
                   'tideHeight': tide,
                   'sessions': sessions})


# -----------------------------------------------------------------------------------
# bootstrap DB with historical data
def databootstrap(request):
    # open surf data bootstrap file
    with open("surfinfo/surfdatabootstrap.json", "r") as read_file:
        surfData = json.load(read_file)

    # rudimentary check to see if surfdatabootstrap.json has already been loaded into DB
    if SurfSession.objects.filter(spotName=surfData[0]['spotName']).exists():
        # already bootstrapped, GTFO
        return HttpResponse("already bootstrapped bro, ADIOS MOTHAFUCKA")
    else:
        # IT'S BOOTSTRAPPIN TIME

        # for each entry in surfData, create + save a new SurfSession, up to 3 new Swells, and 2 new Tides
        for each in surfData:
            sessionUtcOffsetTz = timezone(offset=timedelta(hours=each['spotUtcOffset']))

            processedSession = SurfSession(spotName=each['spotName'],
                                           surflineId=each['surflineId'],
                                           spotUtcOffset=each['spotUtcOffset'],
                                           timeIn=datetime.fromtimestamp(each['timestampIn'], tz=sessionUtcOffsetTz),
                                           timeOut=datetime.fromtimestamp(each['timestampOut'], tz=sessionUtcOffsetTz),
                                           waveCount=each['waveCount'],
                                           surfScore=each['surfScore'],
                                           crowdScore=each['crowdScore'],
                                           board='NONE')

            # print(processedSession)
            # print("utcOffset: " + str(processedSession.spotUtcOffset))
            # print("in: " + str(processedSession.timeIn))
            # print("out: " + str(processedSession.timeOut))
            # print("surflineId: " + str(processedSession.surflineId))
            # print("surfScore: " + str(processedSession.surfScore))
            # print("crowdScore: " + str(processedSession.crowdScore))
            # print("wave count: " + str(processedSession.waveCount))
            processedSession.save()

            # add a max of 3 swells, as long as height is non-zero
            if each["swell1Height"] != 0:
                swell1 = Swell(height=each['swell1Height'],
                               period=each['swell1Period'],
                               direction=each['swell1Direction'])
                swell1.save()
                processedSession.swells.add(swell1)
                # print("swell 1: " + str(swell1))

            if each["swell2Height"] != 0:
                swell2 = Swell(height=each['swell2Height'],
                               period=each['swell2Period'],
                               direction=each['swell2Direction'])
                swell2.save()
                processedSession.swells.add(swell2)
                # print("swell 2: " + str(swell2))

            if each["swell3Height"] != 0:
                swell3 = Swell(height=each['swell3Height'],
                               period=each['swell3Period'],
                               direction=each['swell3Direction'])
                swell3.save()
                processedSession.swells.add(swell3)
                # print("swell 3: " + str(swell3))

            # add start and end tide
            startTide = Tide(timestamp=datetime.fromtimestamp(each['tideStartTimestamp'], tz=sessionUtcOffsetTz),
                             height=each['tideStartHeight'],
                             type='NORMAL')
            startTide.save()
            processedSession.tides.add(startTide)
            # print("start tide: " + str(startTide))

            endTide = Tide(timestamp=datetime.fromtimestamp(each['tideEndTimestamp'], tz=sessionUtcOffsetTz),
                           height=each['tideEndHeight'],
                           type='NORMAL')
            endTide.save()
            processedSession.tides.add(endTide)
            # print("end tide: " + str(endTide))

            # print("***")
            # print("")

    return HttpResponse("all done bro, historical sessions locked and loaded")
