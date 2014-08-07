from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from soundcloudapi.models import Track, Criticize, JsonSerializable


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
    def get_criticize(cls, posted):
        track_id = posted.get(u"track_id")
        criticize_type = posted.get(u"criticize_type")
        value = posted.get(u"value")

        if track_id and criticize_type and value:
            return Criticize(track_id, criticize_type, value)
        else:
            return None

    @classmethod
    def list(cls, request):
        """
        send list of tracks
        """
        # request.QUERY_PARAMS

        return cls.__make_response(None, cls.get_criticize(request))

    @classmethod
    def criticize(cls, request):
        criticize = cls.get_criticize(request.POST)

        if criticize:
            cls.add_criticize(request, criticize)
            return cls.__make_response(criticize, cls.get_criticize(request))
        else:
            #todo need error handling
            return None

    @classmethod
    def __make_response(cls, criticize, history=None):
        return HttpResponse(cls.evaluate(criticize, history))

    @classmethod
    def evaluate(cls, criticize, history=None):
        track = Track()

        # get tracks by criticizes
        tracks = track.find(criticize.to_conditions())
        selected = Track(criticize.get_track())

        # evaluate tracks
        tracks_evaluated = track.calc_score(tracks, selected)

        # criticize patterns
        patterns = track.make_pattern(tracks, selected)
        patterns_list = map(lambda p: p.to_dict(), patterns)

        serialized_tracks = JsonSerializable.to_json_array(tracks_evaluated)
        return {"tracks": serialized_tracks, "criticize": patterns_list}


# Create your views here.
def index(request):
    return render(request, "soundcloudapi/index.html")
