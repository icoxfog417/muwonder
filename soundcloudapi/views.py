from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from urllib2 import HTTPError
from time import sleep
import json
import random
from soundcloudapi.models import Track, TrackCriticize, TrackCriticizePattern


class RecommendApi(object):
    TRACK_COUNT_BASE = 100
    TRACK_TRIAL_LIMIT = 3

    def __init__(self):
        pass

    @classmethod
    def recommends(cls, request):
        criticize = None
        limit = 20  # todo:get limit by parameter

        # need try catch statement
        if request.method == "POST":
            criticize = cls.make_criticize(request.POST)
            SessionManager.add_session(request, SessionManager.CRITICIZE_SESSION, criticize.make_conditions())
        else:
            # initialize when get
            SessionManager.set_session(request, SessionManager.CRITICIZE_SESSION, [])
            SessionManager.set_session(request, SessionManager.TRACK_SESSION, [])

        # get from session
        history = SessionManager.get_session(request, SessionManager.CRITICIZE_SESSION)
        tracks = SessionManager.get_session(request, SessionManager.TRACK_SESSION)
        tracks = Track().load_dict(tracks)  # deserialization

        # load tracks if criticism is none
        if not criticize:
            tracks = cls.get_tracks(criticize, history, tracks)

        # evaluate tracks
        evaluated = cls.evaluate(tracks, criticize, history)

        # to dictionary
        serialized_evaluated = map(lambda s: {"score": s.score, "item": s.item.to_dict(), "score_detail": s.score_detail}, evaluated)

        # store to session
        SessionManager.set_session(request, SessionManager.TRACK_SESSION, map(lambda s: s["item"], serialized_evaluated))

        if limit > 0:
            serialized_evaluated = serialized_evaluated[:limit]

        jsonized = json.dumps(serialized_evaluated)
        return HttpResponse(jsonized, content_type="application/json")

    @classmethod
    def make_criticize(cls, posted):
        track_id = posted.get(u"track_id")
        criticize_type = posted.get(u"criticize_type")
        value = posted.get(u"value")

        if track_id and criticize_type:
            return TrackCriticize(track_id, criticize_type, value)
        else:
            raise Exception("Can not create criticize by POST data. track_id or criticizy_type parameter is missing")

    @classmethod
    def get_tracks(cls, criticize, history=None, initial_tracks=None):
        track = Track()
        tracks = initial_tracks
        trial_count = 0

        while trial_count < RecommendApi.TRACK_TRIAL_LIMIT or len(tracks) <= RecommendApi.TRACK_COUNT_BASE:
            try:
                # get tracks by criticizes
                condition = TrackCriticize.get_default_conditions() if not criticize else criticize.make_conditions()
                if len(tracks) > 0:
                    condition["offset"] = len(tracks)

                new_tracks = track.find(condition)
                tracks += filter(lambda t: t.id not in [t.id for t in tracks], new_tracks)
            except HTTPError as ex:
                pass

            trial_count += 1
            sleep(0.5)

        tracks = tracks[:RecommendApi.TRACK_COUNT_BASE]

        return tracks

    @classmethod
    def evaluate(cls, tracks, criticize, history=None):
        evaluator = Track.make_evaluator(TrackCriticizePattern)
        selected = None
        chosen_tracks = list(tracks)

        if criticize:
            # filter by criticize
            selected = next(iter(filter(lambda t: t.id == criticize.track_id, tracks)), None)
            chosen_tracks = filter(lambda t: criticize.is_fit_criticize(t), tracks)

            #todo blush up how to load tracks
            if len(chosen_tracks) == 0:
                chosen_tracks = cls.get_tracks(criticize, history)

        else:
            selected = random.sample(tracks, 1)[0]

        tracks_evaluated = evaluator.calc_score(chosen_tracks, selected)

        return tracks_evaluated

    @classmethod
    def get_criticize_pattern(cls, request):
        if request.method == "POST":
            track_id = request.POST.get(u"track_id")

            tracks = SessionManager.get_session(request, SessionManager.TRACK_SESSION)
            tracks = Track().load_dict(tracks)  # deserialization

            limit = 3   #todo receive it from parameter

            patterns = cls.make_criticize_pattern(track_id, tracks)
            serialized_patterns = map(lambda c: c.to_dict(), patterns[:limit])

            jsonized = json.dumps(serialized_patterns)
            return HttpResponse(jsonized, content_type="application/json")
        else:
            raise Exception("you have to use POST method when access the get_criticize_pattern.")

    @classmethod
    def make_criticize_pattern(cls, target_track_id, tracks):
        criticize = TrackCriticize(target_track_id, 0)

        track = next(iter(filter(lambda t: t.id == target_track_id, tracks)), None)
        if track is None:
            track = criticize.get_track()

        evaluator = Track.make_evaluator(TrackCriticizePattern)
        criticize_patterns = evaluator.make_pattern(tracks, track)

        return criticize_patterns


class SessionManager(object):
    CRITICIZE_SESSION = "CRITICIZE_STORE_KEY"
    TRACK_SESSION = "TRACK_STORE_KEY"

    def __init__(self):
        pass

    @classmethod
    def get_session(cls, request, key):
        if request.session.get(key, False):
            return request.session.get(key)
        else:
            return []

    @classmethod
    def add_session(cls, request, key, value):
        cs = request.session.get(key, False)
        if not cs:
            cs = []

        cs.append(value)
        request.session[key] = cs

    @classmethod
    def set_session(cls, request, key, value):
        request.session[key] = value

# Create your views here.
@ensure_csrf_cookie
def index(request):
    return render(request, "soundcloudapi/index.html")
