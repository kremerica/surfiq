from datetime import datetime

from django.test import TestCase

from .models import SurfSession, Swell, Tide


# Create your tests here.
class SurfSessionModelTests(TestCase):
    def test_sanity_check(self):
        self.assertIs(True, True)

    # make sure this is the first test to write Swell, Tide, or SurfSession objects to DB
    def test_data_bootstrap(self):
        """
        test_data_bootstrap() returns True if first bootstrap call succeeds, spot check for a surf session
        verifies correctness, and then second call to bootstrap exits without bootstrapping
        :return:
        """

        self.assertIs(SurfSession.dataBootstrap(), True)

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
        self.assertIs(SurfSession.dataBootstrap(), False, msg="Second bootstrap call returned True")

        # recount surf sessions, make sure the number hasn't changed
        self.assertEqual(SurfSession.objects.all().count(), 123, msg="Second bootstrap call added stuff")

    def test_add_surf_session(self):
        """
        test_add_surf_session() returns True if a session can be successfully added to DB, False otherwise,
        using Steamer Lane as the test spot
        :param self:
        :return:
        """

        right_now = datetime.now()

        input_session = SurfSession.fromSurfline(spotId="5842041f4e65fad6a7708805",
                                                 spotName="Steamer Lane",
                                                 startTime=right_now.time(),
                                                 endTime=right_now.time(),
                                                 surfScore=3,
                                                 crowdScore=3,
                                                 waveCount=-1)

        # confirm that the test session was added to DB by retrieving and comparing
        database_session = SurfSession.objects.get(id=input_session.id)

        self.assertEqual(input_session.surflineId, database_session.surflineId)
