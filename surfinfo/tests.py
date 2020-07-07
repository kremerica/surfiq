from datetime import datetime, timezone, timedelta
from django.test import TestCase, Client
from django.urls import reverse
import json

from .models import SurfSession, Swell, Tide


# Create your tests here.
class SurfSessionModelTests(TestCase):
    def test_sanity_check(self):
        self.assertIs(True, True)

    # make sure this is the first test to write Swell, Tide, or SurfSession objects to DB
    def test_data_bootstrap(self):
        """
        verifies boostrapped surf data is sane and bootstrapping is idempotent
        :return:
        """

        self.assertIs(SurfSession.data_bootstrap(), True)

        # count surf sessions loaded up
        self.assertEqual(SurfSession.objects.all().count(), 123)

        # count swells with direction of 12 (51) to verify Swells loaded up correction
        self.assertEqual(Swell.objects.filter(period=12).count(), 51)

        # test linkage of Swells and SurfSessions (42 sessions with a swell at 15s)
        self.assertEqual(SurfSession.objects.filter(swells__period=12).distinct().count(), 42)

        # count tides with height <= 0 ft (22)
        self.assertEqual(Tide.objects.filter(height__lt=-0).count(), 22)

        # test linkage of Tides and SurfSessions (17 sessions with a tide <= 0 ft)
        self.assertEqual(SurfSession.objects.filter(tides__height__lt=0).distinct().count(), 17)

        # try to bootstrap again, should return false
        self.assertIs(SurfSession.data_bootstrap(), False, msg="Second bootstrap call returned True")

        # recount surf sessions, make sure the number hasn't changed
        self.assertEqual(SurfSession.objects.all().count(), 123, msg="Second bootstrap call added stuff")

    def test_swell_comparisons(self):
        """
        test swell comparisons (==, <, <=, >, >=)
        :return:
        """
        swell1 = Swell(height=2.2,
                       period=15,
                       direction=215)

        swell2 = Swell(height=2.1,
                       period=12,
                       direction=295)

        self.assertEqual(swell1.power, 3.4)
        self.assertEqual(swell2.power, 2.5)

        self.assertNotEqual(swell1, swell2)
        self.assertGreater(swell1, swell2)
        self.assertGreaterEqual(swell1, swell1)
        self.assertLess(swell2, swell1)
        self.assertLessEqual(swell2, swell2)
        self.assertEqual(swell1, swell1)

    def test_get_surfline_swells(self):
        """
        smoke test for getting spot and region swells from Surfline
        :return:
        """

        right_now = datetime.now(tz=timezone(offset=timedelta(hours=-7)))

        # get swells for Steamer's
        spotSwells = Swell.get_surfline_swells(surflineId="5842041f4e65fad6a7708805", subregionFlag=False, surfDatetime=right_now)

        # get swells for Santa Cruz County
        regionSwells = Swell.get_surfline_swells(surflineId="58581a836630e24c44879011", subregionFlag=True, surfDatetime=right_now)

        self.assertGreater(len(spotSwells), 0)
        self.assertGreater(len(regionSwells), 0)

    def test_get_surfline_tides(self):
        """
        smoke test for getting spot tides from Surfline
        :return:
        """

        start_time = datetime.now(tz=timezone(offset=timedelta(hours=-7)))
        end_time = start_time + timedelta(hours=1)

        # grab tides for Steamer's
        spotTides = Tide.get_surfline_tides(surflineId="5842041f4e65fad6a7708805",
                                            startDatetime=start_time,
                                            endDatetime=end_time)

        self.assertGreater(len(spotTides), 0)

    def test_add_surf_session(self):
        """
        tests that a session can be added from Surfline
        :param self:
        :return:
        """

        right_now = datetime.now()

        input_session = SurfSession.from_surfline(spotId="5842041f4e65fad6a7708805",
                                                  spotName="Steamer Lane",
                                                  startTime=right_now.time(),
                                                  endTime=right_now.time(),
                                                  surfScore=3,
                                                  crowdScore=3,
                                                  waveCount=-1)

        # confirm that the test session was added to DB by retrieving and comparing
        database_session = SurfSession.objects.get(id=input_session.id)

        self.assertEqual(input_session.surflineId, database_session.surflineId)

# if failure due to "Missing staticfiles manifest...", cmd line: python manage.py collectstatic
class TestViews(TestCase):
    def setUp(self):
        self.client = Client()

        self.session1 = SurfSession.from_surfline(spotId="5842041f4e65fad6a7708805",
                                                  spotName="Steamer Lane",
                                                  startTime=datetime.now().time(),
                                                  endTime=datetime.now().time(),
                                                  surfScore=3,
                                                  crowdScore=3,
                                                  waveCount=-1)

    def test_surfinfo_index_GET(self):
        response = self.client.get(reverse('index'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'surfinfo/index.html')

    def test_addsession_GET(self):
        response = self.client.get(reverse('add_session'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'surfinfo/sessionform.html')

    def test_addsession_POST_adds_new_session(self):
        response = self.client.post(reverse('add_session'), {
            'surfSpot': 'Steamer Lane:5842041f4e65fad6a7708805',
            'startTime': '06:00',
            'endTime': '08:00',
            'surfScore': 3,
            'crowdScore': 3,
            'waveCount': -1,
        })

        self.assertRedirects(response,
                             reverse('session_thankyou') + '?sessionid=2',
                             status_code=302,
                             target_status_code=200,
                             msg_prefix='',
                             fetch_redirect_response=True)

    def test_session_thankyou_GET(self):
        response = self.client.get(reverse('session_thankyou') + '?sessionid=1')

        # basic sanity check
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'surfinfo/sessionthankyou.html')

        # test context
        self.assertEqual(response.context['surfsession'].spotName, 'Steamer Lane')

    def test_data_bootstrap_GET(self):
        response = self.client.get(reverse('data_bootstrap'))

        self.assertEqual(response.status_code, 200)
