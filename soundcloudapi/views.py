from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from soundcloudapi.models import Track, Criticize, CriticizeType, JsonSerializable
import json


class RecommendApi(object):

    CRITICIZE_SESSION_KEY = "criticize_key"

    def __init__(self):
        pass

    @classmethod
    def get_criticize(cls, request):
        if request.session.get(cls.CRITICIZE_SESSION_KEY, False):
            return request.session.get(cls.CRITICIZE_SESSION_KEY)
        else:
            return []

    @classmethod
    def add_criticize(cls, request, criticize):
        cs = request.session.get(cls.CRITICIZE_SESSION_KEY, False)
        if not cs:
            cs = []

        cs.append(criticize.to_dict())
        request.session[cls.CRITICIZE_SESSION_KEY] = cs

    @classmethod
    def make_criticize(cls, posted):
        track_id = posted.get(u"track_id")
        criticize_type = posted.get(u"criticize_type")
        value = posted.get(u"value")

        if track_id and criticize_type:
            return Criticize(track_id, criticize_type, value)
        else:
            return None

    @classmethod
    def dispatch(cls, request):
        if request.method == "POST":
            return cls.criticize(request)
        else:
            return cls.list(request)

    @classmethod
    def list(cls, request):
        """
        send list of tracks
        """
        # request.QUERY_PARAMS

        return cls.__make_response(None, cls.get_criticize(request))

    @classmethod
    def criticize(cls, request):
        criticize = cls.make_criticize(request.POST)

        if criticize:
            cls.add_criticize(request, criticize)
            return cls.__make_response(criticize, cls.get_criticize(request))
        else:
            #todo need error handling
            return None

    @classmethod
    def __make_response(cls, criticize, history, limit=20):
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
        tracks = track.find(Criticize.get_default_conditions() if not criticize else criticize.to_conditions())

        selected = None
        if criticize:
            selected = Track(criticize.get_track())
        elif len(tracks) > 0:
            selected = tracks[0]

        result = {"tracks": [], "criticize": []}
        if selected:
            # evaluate tracks
            evaluator = Track.make_evaluator()
            tracks_evaluated = evaluator.calc_score(tracks, selected)

            # criticize patterns
            patterns = evaluator.make_pattern(tracks, selected)
            pattern_list = map(lambda p: p.to_dict(Criticize.customize_pattern_text), patterns)

            serialized_tracks = map(lambda scored: scored.item.to_dict(), tracks_evaluated)
            result["tracks"] = serialized_tracks
            result["criticize"] = pattern_list

        return result


# Create your views here.
def index(request):
    return render(request, "soundcloudapi/index.html")
