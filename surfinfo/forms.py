from django import forms
from datetime import datetime, time

class TimeInput(forms.TimeInput):
    input_type = "time"

class AddSessionForm(forms.Form):
    # surf spot choice values are ':' delimited pairs of surf spot name and surfline ID
    # should be cleaned up to something more scalable
    SURFSPOT_CHOICES = [
        ('Santa Cruz County', (
                ('Steamer Lane:5842041f4e65fad6a7708805', 'Steamer Lane'),
                ('Pleasure Point:5842041f4e65fad6a7708807', 'Pleasure Point'),
                ('The Hook:584204204e65fad6a7709996', 'The Hook'),
                ('Four Mile:5842041f4e65fad6a7708981', 'Four Mile'),
                ('Waddell Creek:5842041f4e65fad6a7708980', 'Waddell Creek'),
                ('Scott Creek:5842041f4e65fad6a7708982', 'Scott Creek'),
                ('26th Ave:5842041f4e65fad6a770898a', '26th Ave'),
                ('Manresa:5842041f4e65fad6a770898e', 'Manresa'),
            ),
        ),
        ('San Francisco County', (
                ('Ocean Beach SF:5842041f4e65fad6a77087f8', 'Ocean Beach SF'),
            ),
        ),
        ('San Mateo County', (
                ('Linda Mar, Pacifica:5842041f4e65fad6a7708976', 'Linda Mar, Pacifica'),
            ),
        ),
        ('None of these?', (
                ('NEW SPOT:NONE', 'REQUEST NEW SPOT'),
            ),
        )
    ]

    SURFSCORE_CHOICES = (
        (5, 'Legendary'),
        (4, 'Really fun'),
        (3, 'Fun, worth repeating'),
        (2, 'Meh, it was OK'),
        (1, 'Better off not going'),
        (0, 'Unsurfable'),
    )

    CROWDSCORE_CHOICES = (
        (5, 'Empty'),
        (4, 'A few people out'),
        (3, 'Busy, but not too crowded'),
        (2, 'Too crowded'),
        (1, 'Shit show'),
    )

    surfSpot = forms.ChoiceField(label="Where?", choices=SURFSPOT_CHOICES)
    startTime = forms.TimeField(label="Time in", widget=TimeInput)
    endTime = forms.TimeField(label="Time out", widget=TimeInput)

#    waveCount = forms.IntegerField(label="How many waves?")

    surfScore = forms.ChoiceField(label="How fun?", choices=SURFSCORE_CHOICES, initial=2)
    crowdScore = forms.ChoiceField(label="Crowded?", choices=CROWDSCORE_CHOICES, initial=3)

    def clean(self):
        startTime = self.cleaned_data['startTime']
        endTime = self.cleaned_data['endTime']

        if endTime < startTime:
            self.add_error('endTime', 'End time is before start time :(')

class AddSurfSpot(forms.Form):
    spotName = forms.CharField(label="Spot name")