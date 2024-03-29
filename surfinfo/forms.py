from django import forms
from datetime import datetime, timedelta

class TimeInput(forms.TimeInput):
    input_type = "time"


class DatetimeInput(forms.DateTimeInput):
    input_type = "datetime-local"


class AddSessionForm(forms.Form):
    # surf spot choice values are ":" delimited pairs of surf spot name and surfline ID
    # should be cleaned up to something more scalable
    SURFSPOT_CHOICES = [
        ("Santa Cruz County", (
            ("Steamer Lane:5842041f4e65fad6a7708805", "Steamer Lane"),
            ("Pleasure Point:5842041f4e65fad6a7708807", "Pleasure Point"),
            ("Sewers:5842041f4e65fad6a7708807", "Sewers"),
            ("Rockview:5842041f4e65fad6a7708807", "Rockview"),
            ("The Hook:584204204e65fad6a7709996", "The Hook"),
            ("Four Mile:5842041f4e65fad6a7708981", "Four Mile"),
            ("Waddell, Middle:5842041f4e65fad6a7708980", "Waddell, Middle"),
            ("Waddell, South Reefs:5842041f4e65fad6a7708980", "Waddell, South Reefs"),
            ("Scott Creek:5842041f4e65fad6a7708982", "Scott Creek"),
            ("26th Ave:5842041f4e65fad6a770898a", "26th Ave"),
            ("Manresa:5842041f4e65fad6a770898e", "Manresa"),
            ("Capitola:5842041f4e65fad6a7708ddf", "Capitola"),
            ),
         ),
        ("San Francisco County", (
            ("Ocean Beach, Sloat:5842041f4e65fad6a77087f8", "Ocean Beach, Sloat"),
            ("Ocean Beach, Balboa:5842041f4e65fad6a77087f8", "Ocean Beach, Balboa"),
            ("Ocean Beach, Noriega:5842041f4e65fad6a77087f8", "Ocean Beach, Noriega"),
            ),
        ),
        ("San Mateo County", (
            ("Linda Mar, Pacifica:5842041f4e65fad6a7708976", "Linda Mar, Pacifica"),
            ),
        ),
        ("North San Diego", (
            ("Seaside Reef:5842041f4e65fad6a77088b3", "Seaside Reef"),
            ),
        ),
        ("South San Diego", (
            ("Black's:5842041f4e65fad6a770883b", "Black's"),
            ("Ocean Beach Jetty:5842041f4e65fad6a770883f", "Ocean Beach Jetty"),
            ),
        ),
        ("None of these?", (
            ("NEW SPOT:NONE", "REQUEST NEW SPOT"),
            ),
        )
    ]

    SURFSCORE_CHOICES = (
        (5, "Legendary"),
        (4, "Really fun"),
        (3, "Fun, worth repeating"),
        (2, "Meh, it was OK"),
        (1, "Better off not going"),
        (0, "Unsurfable"),
    )

    CROWDSCORE_CHOICES = (
        (5, "Empty"),
        (4, "A few people out"),
        (3, "Busy, but not too crowded"),
        (2, "Too crowded"),
        (1, "Shit show"),
    )

    surfSpot = forms.ChoiceField(label="Where?", choices=SURFSPOT_CHOICES)
    startTime = forms.TimeField(label="Time in", widget=TimeInput)
    endTime = forms.TimeField(label="Time out", widget=TimeInput)

    #    waveCount = forms.IntegerField(label="How many waves?")

    surfScore = forms.ChoiceField(label="How fun?", choices=SURFSCORE_CHOICES, initial=2)
    crowdScore = forms.ChoiceField(label="Crowded?", choices=CROWDSCORE_CHOICES, initial=3)

    def clean(self):
        startTime = self.cleaned_data["startTime"]
        endTime = self.cleaned_data["endTime"]

        if endTime < startTime:
            self.add_error("endTime", "End time is before start time :(")


class AddSurfSpot(forms.Form):
    spotName = forms.CharField(label="Spot name")


class SessionMatchesConditions(forms.Form):
    #    SURFREGION_CHOICES = (
    #        ("Santa Cruz County", "Santa Cruz County"),
    #        ("San Mateo County", "San Mateo County"),
    #        ("San Francisco County", "San Francisco County"),
    #    )

    # time + location based match
    #    surfDatetime = forms.DateTimeField(label="When?", required=False)
    #    surfRegion = forms.ChoiceField(label="Where?", choices=SURFREGION_CHOICES, initial=1)

    # conditions based match
    swellHeight = forms.DecimalField(label="Swell height")
    swellPeriod = forms.IntegerField(label="Swell period")
    swellDirection = forms.IntegerField(label="Swell direction")
    tideHeight = forms.DecimalField(label="Tide height")

    def clean(self):
        swellHeight = self.cleaned_data["swellHeight"]
        swellPeriod = self.cleaned_data["swellPeriod"]
        swellDirection = self.cleaned_data["swellDirection"]

        if swellHeight < 0:
            self.add_error("swellHeight", "Swell height can't be negative")

        if swellPeriod < 0:
            self.add_error("swellPeriod", "Swell period can't be negative")

        if swellDirection < 0 or swellDirection > 360:
            self.add_error("swellDirection", "Swell direction must be between 0 and 360")


class SessionMatchesTimeAndPlace(forms.Form):
    SURFREGION_CHOICES = (
        ("58581a836630e24c44879011", "Santa Cruz County"),
        ("5cc73566c30e4c0001096989", "San Mateo County"),
        ("58581a836630e24c44879010", "San Francisco County"),
        ("58581a836630e24c44878fd7", "North San Diego"),
        ("58581a836630e24c4487900d", "South San Diego"),
    )

    # time + location based match
    surfDatetime = forms.DateTimeField(label="When?", widget=DatetimeInput)
    surfRegion = forms.ChoiceField(label="Where?", choices=SURFREGION_CHOICES, initial=1)

    def clean(self):
        MAX_SURFLINE_LOOKAHEAD_DAYS = 6

        surfDatetime = self.cleaned_data["surfDatetime"]

        if surfDatetime - datetime.now() > timedelta(days=MAX_SURFLINE_LOOKAHEAD_DAYS):
            self.add_error("surfDatetime", "Max 6 days in the future, bro")
