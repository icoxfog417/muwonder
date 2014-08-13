from django.http import HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from soundcloudapi.models import Track, TrackCriticize, TrackCriticizePattern
import json


class RecommendApi(object):

    SESSION_STORE_KEY = "SESSION_STORE_KEY"

    def __init__(self):
        pass

    @classmethod
    def get_session(cls, request):
        if request.session.get(cls.SESSION_STORE_KEY, False):
            return request.session.get(cls.SESSION_STORE_KEY)
        else:
            return []

    @classmethod
    def add_session(cls, request, criticize):
        cs = request.session.get(cls.SESSION_STORE_KEY, False)
        if not cs:
            cs = []

        cs.append(criticize.values)
        request.session[cls.SESSION_STORE_KEY] = cs

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
    def dispatch(cls, request):
        criticize = None
        limit = 20  # todo:get limit by parameter

        # need try catch statement
        if request.method == "POST":
            criticize = cls.make_criticize(request.POST)
            cls.add_session(request, criticize)

        history = cls.get_session(request)
        result = cls.evaluate(criticize, history)

        if limit > 0:
            result["tracks"] = result["tracks"][:limit]
            result["criticize"] = result["criticize"][:limit]

        jsonized = json.dumps(result)
        return HttpResponse(jsonized, content_type="application/json")

    @classmethod
    def evaluate(cls, criticize, history=None):
        track = Track()

        # get tracks by criticizes
        condition = TrackCriticize.get_default_conditions() if not criticize else criticize.to_conditions()
        tracks = track.find(condition)

        selected = None
        if criticize:
            selected = Track(criticize.get_track())
        elif len(tracks) > 0:
            selected = tracks[0]

        result = {"tracks": [], "criticize": []}
        if selected:
            # evaluate tracks
            evaluator = Track.make_evaluator(TrackCriticizePattern)
            tracks_evaluated = evaluator.calc_score(tracks, selected)

            # criticize patterns
            patterns = evaluator.make_pattern(tracks, selected)
            pattern_list = map(lambda p: p.to_dict(), patterns)

            serialized_tracks = map(lambda scored: scored.item.to_dict(), tracks_evaluated)
            result["tracks"] = serialized_tracks
            result["criticize"] = pattern_list

        return result


# Create your views here.
@ensure_csrf_cookie
def index(request):
    return render(request, "soundcloudapi/index.html")
