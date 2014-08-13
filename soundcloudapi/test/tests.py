from django.test import TestCase
from soundcloudapi.views import RecommendApi
from soundcloudapi.models import Track, TrackCriticizePattern, TrackCriticizeType


# Create your tests here.
class TrackTestCase(TestCase):

    def setUp(self):
        pass

    def test_tracks(self):
        track = Track()
        tracks = track.find({"q": "Hiatus", "created_at": {"from": "2014-01-01 00:00:00"}, "limit": 5})
        for t in tracks:
            print(t.title + "/" + t.genre if t.genre else t.title)

    def test_proposal_criticize_to_condition(self):
        # bpm exist. but genre is not target
        cr = {u"track_id": u"146413237", u"criticize_type": u"0", u"value": u"+:genre,bpm,created_at"}
        print self.__test_track(cr)

        # genre is exist but bpm is not
        cr = {u"track_id": u"140176339", u"criticize_type": u"0", u"value": u"+:genre,bpm,created_at"}
        print self.__test_track(cr)

    def test_evaluate(self):
        cr = {u"track_id": u"140176339", u"criticize_type": u"0", u"value": u"+:genre,bpm,created_at"}

        # bpm exist. but genre is not target
        # resp = self.__evaluate_track(u"146413237", cr)

        # genre is exist but bpm is not
        resp = self.__evaluate_track(cr)
        print(resp["tracks"])
        print(resp["criticize"])

    def __test_track(self, cr_pattern):
        criticize = RecommendApi.make_criticize(cr_pattern)

        condition = criticize.to_conditions()
        return condition

    def __evaluate_track(self, cr_pattern):
        criticize = RecommendApi.make_criticize(cr_pattern)
        return RecommendApi.evaluate(criticize)