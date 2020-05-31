from django import forms
from datetime import datetime, time

class TimeInput(forms.TimeInput):
    input_type = "time"

class AddSessionForm(forms.Form):
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

    startTime = forms.TimeField(label="Time in", widget=TimeInput)
    endTime = forms.TimeField(label="Time out", widget=TimeInput, initial=datetime.now().time)

    waveCount = forms.IntegerField(label="How many waves?")

    surfScore = forms.ChoiceField(label="How good was it?", choices=SURFSCORE_CHOICES, initial=3)
    crowdScore = forms.ChoiceField(label="How crowded was it?", choices=CROWDSCORE_CHOICES, initial=3)

    def clean(self):
        startTime = self.cleaned_data['startTime']
        endTime = self.cleaned_data['endTime']

        if endTime < startTime:
            self.add_error('endTime', 'Time machines forbidden, end time needs to be after start time')
