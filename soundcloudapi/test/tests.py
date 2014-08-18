# -*- coding: utf-8 -*-
from django.test import TestCase
from soundcloudapi.views import RecommendApi
from soundcloudapi.models import Track, TrackCriticize, TrackCriticizePattern, TrackCriticizeType
import random


def print_title(test_case):
    def wrapper(*args, **kwargs):
        print("@" + test_case.__name__ + "-------------------------------------------")
        return test_case(*args, **kwargs)

    return wrapper


# Create your tests here.
class TrackTestCase(TestCase):

    def setUp(self):
        self.tracks = []
        track = Track()
        tracks = track.find({"genre": u"rock", "created_at": {"from": "2014-01-01 00:00:00"}, "limit": 100})
        self.print_tracks(tracks[:10], lambda t: self.tracks.append(t))

    @print_title
    def serialize_tracks(self):
        Track().load_dict(self.tracks)

    @print_title
    def test_evaluate_init(self):
        evaluated = RecommendApi.evaluate(self.tracks, None)
        self.print_tracks(evaluated[:10])

    @print_title
    def test_make_criticize_pattern(self):
        selected_track = random.sample(self.tracks, 1)[0]
        patterns = RecommendApi.make_criticize_pattern(selected_track.id, self.tracks)
        for p in [p.to_dict() for p in patterns]:
            print(p["pattern"], p["text"])

    @print_title
    def test_evaluate_with_criticize(self):
        selected_track = random.sample(self.tracks, 1)[0]
        patterns = RecommendApi.make_criticize_pattern(selected_track.id, self.tracks)

        selected_pattern = random.sample(patterns, 1)[0]
        criticize = TrackCriticize(selected_track.id, TrackCriticizeType.Pattern, selected_pattern.pattern)

        evaluated = RecommendApi.evaluate(self.tracks, criticize)

        print("selected item -------------------------")
        self.print_tracks([selected_track])
        print("selected pattern -------------------------")
        print(criticize.value)
        print("evaluated as below -------------------------")
        self.print_tracks(evaluated[:10])

    @print_title
    def test_genre_to_score(self):
        self.assertEqual(Track.genre_to_score(u"Death Metal"), Track.genre_to_score(u"metal"))

    @print_title
    def test_make_criticize_by_parameter(self):
        selected_record = random.sample(self.tracks, 1)[0]

        # by parameter
        track_id = selected_record.id
        value = {u"bpm": u"123"}  # dummy bpm value
        parameter_criticism = TrackCriticize(track_id, TrackCriticizeType.Parameter, value)

        parameters = parameter_criticism.make_parameters()
        print(parameters)
        self.assertEqual(parameters[u"bpm"], value[u"bpm"])

        conditions = parameter_criticism.make_conditions()
        print(conditions)
        self.assertEqual(conditions[u"bpm"]["from"], int(value[u"bpm"]) - 20)
        self.assertEqual(conditions[u"bpm"]["to"], int(value[u"bpm"]) + 20)

    @print_title
    def test_make_criticize_by_pattern(self):
        selected_record = random.sample(self.tracks, 1)[0]

        # by parameter
        track_id = selected_record.id
        value = u"-:genre, elapsed"
        pattern_criticism = TrackCriticize(track_id, TrackCriticizeType.Pattern, value)

        parameters = pattern_criticism.make_parameters()
        print(parameters)

        conditions = pattern_criticism.make_conditions()
        print(conditions)

    @print_title
    def test_make_criticize_by_track(self):
        selected_record = random.sample(self.tracks, 1)[0]

        # by parameter
        track_id = selected_record.id
        track_criticism = TrackCriticize(track_id, TrackCriticizeType.Like)

        parameters = track_criticism.make_parameters()
        print(parameters)

        conditions = track_criticism.make_conditions()
        print(conditions)

    def print_tracks(self, tracks, foreach=None):
        for t in tracks:
            if foreach:
                foreach(t)
            print(u"{0}: genre({1}), genre_score({2}), created_at({3}). ".format(t.title, t.genre, t.genre_score(), t.created_at))
