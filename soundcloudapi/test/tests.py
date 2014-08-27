# -*- coding: utf-8 -*-
from django.test import TestCase
from soundcloudapi.views import RecommendApi
from soundcloudapi.models import Track, TrackCriticizeType, ParameterAdapter
import json
import random


def print_title(test_case):
    def wrapper(*args, **kwargs):
        print("@" + test_case.__name__ + "-------------------------------------------")
        return test_case(*args, **kwargs)

    return wrapper


# Create your tests here.
class TrackTestCase(TestCase):

    def setUp(self):
        self.tracks = Track().find({"q": u"the Hiatus", "created_at": {"from": "2014-01-01 00:00:00"}, "limit": 100})
        self.tracks = sorted(self.tracks, key=lambda t: t.playback_count, reverse=True)

    @print_title
    def test_criticize_by_parameter(self):
        pa = ParameterAdapter()
        selected_track = random.sample(self.tracks, 1)[0]

        # by parameter
        criticize_type = TrackCriticizeType.Parameter
        post_parameters = {u"bpm": u"123"}  # dummy bpm value
        parameters = pa.request_to_parameters(criticize_type, selected_track, post_parameters)

        print(map(lambda p: p.__str__(), parameters))

        scored = RecommendApi.get_scored_tracks(parameters, selected_track, self.tracks)
        print("tracks: {0}".format(len(scored)))
        self.print_tracks(map(lambda s: s.item, scored[:10]))

    @print_title
    def test_criticize_by_pattern(self):
        pa = ParameterAdapter()
        selected_track = random.sample(self.tracks, 1)[0]

        # by parameter
        criticize_type = TrackCriticizeType.Pattern
        evaluator = Track.make_evaluator()
        criticize_patterns = evaluator.make_pattern(self.tracks, selected_track)

        pattern = random.sample(criticize_patterns, 1)[0]
        post_parameters = {u"pattern": pattern.pattern}
        parameters = pa.request_to_parameters(criticize_type, selected_track, post_parameters)

        print(map(lambda p: p.__str__(), parameters))

        scored = RecommendApi.get_scored_tracks(parameters, selected_track, self.tracks)
        print("tracks: {0}".format(len(scored)))
        self.print_tracks(map(lambda s: s.item, scored[:10]))

    @print_title
    def test_criticize_by_like(self):
        pa = ParameterAdapter()
        selected_track = random.sample(self.tracks, 1)[0]

        # by parameter
        criticize_type = TrackCriticizeType.Like
        scored = RecommendApi.get_favorite_tracks([], selected_track, self.tracks)
        print("tracks: {0}".format(len(scored)))
        self.print_tracks(map(lambda s: s.item, scored[:10]))


    def print_tracks(self, tracks, foreach=None):
        for t in tracks:
            if foreach:
                foreach(t)
            print(u"{0}: genre({1}), genre_score({2}), created_at({3}). ".format(t.title, t.genre, t.genre_score(), t.created_at))
