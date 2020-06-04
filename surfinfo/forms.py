from django import forms
from datetime import datetime, time

class TimeInput(forms.TimeInput):
    input_type = "time"

class AddSessionForm(forms.Form):
    # surf spot choice values are ':' delimited pairs of surf spot name and surfline ID
    # should be cleaned up to something more scalable
    SURFSPOT_CHOICES = (
        ('Pleasure Point:5842041f4e65fad6a7708807', 'Pleasure Point'),
        ('Steamer Lane:5842041f4e65fad6a7708805', 'Steamer Lane'),
        ('Waddell Creek:5842041f4e65fad6a7708980', 'Waddell Creek'),
        ('Four Mile:5842041f4e65fad6a7708981', 'Four Mile'),
        ('The Hook:584204204e65fad6a7709996', 'The Hook'),
        ('Ocean Beach SF:5842041f4e65fad6a77087f8', 'Ocean Beach SF'),
        ('Linda Mar, Pacifica:5842041f4e65fad6a7708976', 'Linda Mar, Pacifica'),
    )

    SURFSCORE_CHOICES = (
        (5, 'Legendary'),
        (4, 'Good'),
        (3, 'OK'),
        (2, 'Not good'),
        (1, 'Better off not going'),
    )

    CROWDSCORE_CHOICES = (
        (5, 'Empty'),
        (4, 'Handful of people, no impact to wave count'),
        (3, 'Busy, not crowded'),
        (2, 'Crowded, serious reduction in wave count'),
        (1, 'Shit show'),
    )

    surfSpot = forms.ChoiceField(label="Where did you surf?", choices=SURFSPOT_CHOICES)
    startTime = forms.TimeField(label="Time in", widget=TimeInput)
    endTime = forms.TimeField(label="Time out", widget=TimeInput)

    waveCount = forms.IntegerField(label="How many waves?")

    surfScore = forms.ChoiceField(label="How good was it?", choices=SURFSCORE_CHOICES, initial=3)
    crowdScore = forms.ChoiceField(label="How crowded was it?", choices=CROWDSCORE_CHOICES, initial=3)

    def clean(self):
        startTime = self.cleaned_data['startTime']
        endTime = self.cleaned_data['endTime']

        if endTime < startTime:
            self.add_error('endTime', 'Time machines forbidden, end time needs to be after start time')
