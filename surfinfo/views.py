from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from .models import Swell, Tide, SurfSession, SurfSpot
from datetime import datetime, timedelta, date, timezone

from .forms import AddSessionForm, AddSurfSpot, SessionMatchesConditions, SessionMatchesTimeAndPlace


# adding a session
def index(request):
    return render(request, 'surfinfo/index.html')

# adding a session
def addsession(request):
    # if this is a POST request, process form data
    if request.method == 'POST':
        form = AddSessionForm(request.POST)

        if form.is_valid():
            # process the data
            # grab swell info from Surfline API (do this first to get the surf spot UTC offset)
            surfSpotId = form.cleaned_data['surfSpot'].split(':')[1]
            surfSpotName = form.cleaned_data['surfSpot'].split(':')[0]
            startTime = form.cleaned_data['startTime']
            endTime = form.cleaned_data['endTime']
            surfScore = form.cleaned_data['surfScore']
            crowdScore = form.cleaned_data['crowdScore']
            waveCount = -1

            # only process the data if there was a spot selected
            if surfSpotId != 'NONE':
                # create a SurfSession object, save to DB
                todaySession = SurfSession.fromSurfline(spotId=surfSpotId,
                                                        spotName=surfSpotName,
                                                        startTime=startTime,
                                                        endTime=endTime,
                                                        surfScore=surfScore,
                                                        crowdScore=crowdScore,
                                                        waveCount=waveCount)
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
def session_matches_conditions(request):
    form = SessionMatchesConditions()

    tide = request.GET.get('tideHeight', 0)

    swell = Swell(height=request.GET.get('swellHeight', 0),
                  period=request.GET.get('swellPeriod', 0),
                  direction=request.GET.get('swellDirection', 0))

    sessions = SurfSession.getMatchingSessions(swellHeight=swell.height,
                                               swellPeriod=swell.period,
                                               swellDirection=swell.direction,
                                               tideHeight=tide)

    return render(request, 'surfinfo/getmatchingsessions.html',
                  {'form': form,
                   'swellHeight': swell.height,
                   'swellPeriod': swell.period,
                   'swellDirection': swell.direction,
                   'swellPower': swell.power,
                   'tideHeight': tide,
                   'sessions': sessions})


# find matching sessions for conditions at a given time and region
def session_matches_time_and_place(request):
    surfDatetime = request.GET.get('surfDatetime', None)
    surfRegion = request.GET.get('surfRegion', None)

    REGION_TO_SPOT = {'58581a836630e24c44879011': '5842041f4e65fad6a7708805',
                      '5cc73566c30e4c0001096989': '5842041f4e65fad6a7708976',
                      '58581a836630e24c44879010': '5842041f4e65fad6a77087f8'}

    form = SessionMatchesTimeAndPlace()
    displayDatetime = None
    swells = []
    tide = []

    if surfDatetime is not None and surfRegion is not None:
        surfDatetime = datetime.strptime(surfDatetime, '%Y-%m-%dT%H:%M')
        displayDatetime = surfDatetime.strftime('%Y-%m-%dT%H:%M')

        swells = Swell.get_surfline_swells(surflineId=surfRegion,
                                           subregionFlag=True,
                                           surfDatetime=surfDatetime)

        tide = Tide.getSurflineTides(surflineId=REGION_TO_SPOT[surfRegion],
                                     startDatetime=surfDatetime,
                                     endDatetime=surfDatetime + timedelta(milliseconds=1))

    return render(request, 'surfinfo/getconditions.html',
                  {'form': form,
                   'surfDatetime': displayDatetime,
                   'surfRegion': surfRegion,
                   'swells': swells,
                   'junk_threshold': Swell.JUNK_THRESHOLD,
                   'tide': next(iter(tide), None)})


# -----------------------------------------------------------------------------------
# bootstrap DB with historical data
def databootstrap(request):
    if SurfSession.dataBootstrap():
        return HttpResponse("All done bro, historical sessions locked and loaded")
    else:
        return HttpResponse("Already bootstrapped bro, ADIOS MOTHAFUCKA")
