from django.http import HttpResponse
from .models import TestModel
from .models import Swell, Tide, SurfSession
import requests
import json
from datetime import datetime
from django.utils.timezone import make_aware


def index(request):
    r = requests.get(
        'https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=5842041f4e65fad6a7708807&days=1&intervalHours=3&maxHeights=false')
    surfReport = json.loads(r.text)

    print('**swells**')

    for timeBlock in surfReport['data']['wave']:
        #    print('timestamp: ' + str(timeBlock['timestamp']))
        print(datetime.fromtimestamp(timeBlock['timestamp']))

        for each in timeBlock['swells']:
            if each['height'] != 0:
                print(each)
        print()

    test = TestModel(name=request.GET['name'], number=2.2, timestamp=make_aware(datetime.now()))
    test.save()

    # print all TestModel objects to validate that model.save() worked as expected
    print(TestModel.objects.all())

    # return name of current TestModel object to validate query string parameter was read correctly
    return HttpResponse('Hi ' + test.name)