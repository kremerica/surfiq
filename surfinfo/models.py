import requests
import json

from django.db import models
from django.db.models import Avg, Count, Sum, Max
from django.utils.timezone import make_aware

from datetime import datetime, timedelta, timezone



# Create your models here.

class Swell(models.Model):
    height = models.DecimalField(max_digits=4, decimal_places=2)
    period = models.DecimalField(max_digits=4, decimal_places=2)
    direction = models.DecimalField(max_digits=5, decimal_places=2)

    @property
    def power(self):
        """
        calculates the power of a swell, useful for comparisons
        :return:
            kilowatt of power per meter of wave (width, not height)
        """

        FEET_IN_METER = 3.28084

        # wave power equation, more info at https://en.wikipedia.org/wiki/Wave_power
        return round(0.5 * ((float(self.height) / FEET_IN_METER)**2) * float(self.period), 1)

    def __lt__(self, other):
        """
        compares swell power
        :param other:
        :return:
        """
        return self.power < other.power

    def __le__(self, other):
        """
        compares swell power
        :param other:
        :return:
        """
        return self.power <= other.power

    def __gt__(self, other):
        """
        compares swell power
        :param other:
        :return:
        """
        return self.power > other.power

    def __ge__(self, other):
        """
        compares swell power
        :param other:
        :return:
        """
        return self.power >= other.power

    def __eq__(self, other):
        """
        compares swell power and returns True if equal
        :param other:
        :return:
        """
        return self.power == other.power

    def __str__(self):
        return 'height: ' + str(self.height) + ', period: ' + str(self.period) + ', direction: ' + str(self.direction) + ', power: ' + str(self.power)

    @classmethod
    def getSurflineSwells(cls, surflineId, subregionFlag, surfDatetime):
        swells = []

        if subregionFlag:
            surfUrl = 'https://services.surfline.com/kbyg/regions/forecasts/wave?subregionId=' + surflineId + '&days=1&intervalHours=1&maxHeights=false'
        else:
            surfUrl = 'https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=' + surflineId + '&days=1&intervalHours=1&maxHeights=false'

        surf = requests.get(surfUrl)
        surfReport = json.loads(surf.text)

        # get the UTC offset from the surf report, use as timezone in surf session
        # TODO use this to sanity check input datetime
        surfUtcOffset = timezone(offset=timedelta(hours=surfReport['associated']['utcOffset']))

        # print("datetime: " + str(surfDatetime))

        # find the "hour index" that maps to the hour we want swell info for
        startHourIndex = surfDatetime.hour

        # extract all swells for that hour, DO NOT SAVE TO DB
        for each in surfReport['data']['wave'][startHourIndex]['swells']:
            # plop all non-zero-height swells into Swell objects, save to DB, add to surf session
            if each['height'] != 0:
                swells.append(Swell(height=each['height'], period=each['period'], direction=each['direction']))

        return swells

class Tide(models.Model):
    timestamp = models.DateTimeField()
    height = models.DecimalField(max_digits=4, decimal_places=2)
    type = models.CharField(max_length=20)

    def __str__(self):
        return str(self.timestamp) + ': ' + str(self.height) + ' ft, ' + str(self.type)

# not using this one yet, probably shouldn't have created it
class SurfSpot(models.Model):
    surflineId = models.CharField(max_length=100)
    spotName = models.CharField(max_length=100)

class SurfSession(models.Model):
    spotName = models.CharField(max_length=100)
    surflineId = models.CharField(max_length=100)
    spotUtcOffset = models.DecimalField(max_digits=4, decimal_places=2)

    timeIn = models.DateTimeField()
    timeOut = models.DateTimeField()

    waveCount = models.IntegerField()

    # 1 - 5, higher is better
    surfScore = models.IntegerField()

    # 1 - 5, higher is better
    crowdScore = models.CharField(max_length=20)

    # tides throughout a surf session
    tides = models.ManyToManyField(Tide)

    # swells at the start of a surf session
    swells = models.ManyToManyField(Swell)

    board = models.CharField(max_length=100)

    def __str__(self):
        return str(self.spotName) + ': ' + str(self.waveCount) + ' waves'

    # helper method to extract surf info from a URL, create a new SurfSession object with that info, and save to DB
    @classmethod
    def fromSurfline(cls, spotId, spotName, startTime, endTime, surfScore, crowdScore, waveCount):
        surfUrl = 'https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=' + spotId + '&days=1&intervalHours=1&maxHeights=false'
        surf = requests.get(surfUrl)
        surfReport = json.loads(surf.text)

        # grab tide info from Surfline API
        tideUrl = 'https://services.surfline.com/kbyg/spots/forecasts/tides?spotId=' + spotId + '&days=1'
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
        startDateTime = datetime.combine(datetime.now(tz=surfUtcOffset).date(), startTime, tzinfo=surfUtcOffset)
        endDateTime = datetime.combine(datetime.now(tz=surfUtcOffset).date(), endTime, tzinfo=surfUtcOffset)

        # create a SurfSession object for an arbitrary hour for TODAY's surf conditions
        # create and save the base SurfSession object
        todaySession = SurfSession(spotName=spotName,
                                   surflineId=spotId,
                                   spotUtcOffset=surfReport['associated']['utcOffset'],
                                   timeIn=startDateTime,
                                   timeOut=endDateTime,
                                   waveCount=-1,
                                   surfScore=surfScore,
                                   crowdScore=crowdScore,
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

        return todaySession

    # helper method to find matching sessions for a given Swell + Tide
    @classmethod
    def getMatchingSessions(cls, swellHeight, swellPeriod, swellDirection, tideHeight):
        height_factor = 0.25
        period_factor = 1
        direction_factor = 10
        tide_factor = 0.5

        height = float(swellHeight)
        period = float(swellPeriod)
        direction = float(swellDirection)
        tide = float(tideHeight)

        # get a queryset of all sessions
        rawSessions = SurfSession.objects.filter(swells__height__gte=height - height_factor,
                                                 swells__height__lte=height + height_factor,
                                                 swells__period__gte=period - period_factor,
                                                 swells__period__lte=period + period_factor,
                                                 swells__direction__gte=direction - direction_factor,
                                                 swells__direction__lte=direction + direction_factor,
                                                 tides__height__gte=tide - tide_factor,
                                                 tides__height__lte=tide + tide_factor).distinct()

        #    print()
        #    print("*** CONDITIONS ***")
        #    print("*** " + str(height) + "ft " + str(period) + "s at " + str(direction) + "°, tide height " + str(tide))
        #    print("*** PREVIOUS SURFS ***")

        sessions = rawSessions.values("spotName").annotate(Avg("surfScore"), Avg("waveCount"), Count("id")).order_by(
            '-id__count')

        #    if sessions.exists():
        #        for each in sessions:
        #            print(str(each["spotName"]) + ": " +
        #                  str(each["id__count"]) + " sessions, avg score " +
        #                  str(round(each["surfScore__avg"], 1)) + "/5, avg wave count " +
        #                  str(round(each["waveCount__avg"], 1)))
        #
        #    print()

        return sessions


    # bootstrap DB with historical data in surfinfo/surfdatabootstrap
    @classmethod
    def dataBootstrap(cls):
        # open surf data bootstrap file
        with open("surfinfo/surfdatabootstrap.json", "r") as read_file:
            surfData = json.load(read_file)

        # rudimentary check to see if surfdatabootstrap.json has already been loaded into DB
        if SurfSession.objects.filter(spotName=surfData[0]['spotName']).exists():
            # already bootstrapped, GTFO
            return False
        else:
            # IT'S BOOTSTRAPPIN TIME
            # for each entry in surfData, create + save a new SurfSession, up to 3 new Swells, and 2 new Tides
            for each in surfData:
                sessionUtcOffsetTz = timezone(offset=timedelta(hours=each['spotUtcOffset']))

                processedSession = SurfSession(spotName=each['spotName'],
                                               surflineId=each['surflineId'],
                                               spotUtcOffset=each['spotUtcOffset'],
                                               timeIn=datetime.fromtimestamp(each['timestampIn'],
                                                                             tz=sessionUtcOffsetTz),
                                               timeOut=datetime.fromtimestamp(each['timestampOut'],
                                                                              tz=sessionUtcOffsetTz),
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

                # add 3 swells (as long as height is non-zero)
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

        return True
