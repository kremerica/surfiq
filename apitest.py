import requests
import json
from datetime import datetime

# swells
r = requests.get('https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=5842041f4e65fad6a7708807&days=1&intervalHours=3&maxHeights=false')
surfReport = json.loads(r.text)

print('**swells**')

for timeBlock in surfReport['data']['wave']:
#    print('timestamp: ' + str(timeBlock['timestamp']))
    print(datetime.fromtimestamp(timeBlock['timestamp']))

    for each in timeBlock['swells']:
        if each['height'] != 0:
            print(each)
    print()



# tides
r = requests.get('https://services.surfline.com/kbyg/spots/forecasts/tides?spotId=5842041f4e65fad6a7708807&days=1')
tideReport = json.loads(r.text)

# print(tideReport)
print()
print('**tides**')

for timeBlock in tideReport['data']['tides']:
    print(datetime.fromtimestamp(timeBlock['timestamp']))
    print(timeBlock['height'])
    if timeBlock['type'] != 'NORMAL':
        print(timeBlock['type'])
    print()
