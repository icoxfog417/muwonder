from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from urllib2 import HTTPError
from time import sleep
import json
import random
import soundcloud
import secret_settings
from soundcloudapi.models import ParameterAdapter
from soundcloudapi.models import Track, TrackCriticizePattern, TrackCriticizeType


class RecommendApi(object):
    TRACK_COUNT_BASE = 100
    TRACK_TRIAL_LIMIT = 3

    def __init__(self):
        pass

    @classmethod
    def recommends(cls, request):
        track = None
        tracks = []
        pa = ParameterAdapter()
        limit = 20  # todo:get limit by parameter
        response = []

        # get request parameters
        request_body = None
        if request.method == "GET":
            # QueryDict is wrong when GET.
            request_body = request.GET.dict().keys()[0]
        else:
            request_body = request.body

        posted = json.loads(request_body)
        posted_parameters = {} if not u"parameters" in posted else posted[u"parameters"]

        # process by methods
        if request.method == "GET":
            # initialize when get
            SessionManager.set_session(request, SessionManager.CRITICIZE_SESSION, [])
            SessionManager.set_session(request, SessionManager.TRACK_SESSION, [])

            conditions = pa.parameters_to_conditions(posted_parameters)

            tracks = cls.get_tracks(conditions, [])
            if len(tracks) > 0:
                track = tracks[0]
        else:
            track_id = posted[u"track_id"]
            criticize_type = TrackCriticizeType(posted[u"criticize_type"])
            track = cls.__get_track(track_id, tracks)
            tracks = cls.__get_session_tracks(request)  # get from session

            parameters = pa.request_to_parameters(criticize_type, track, posted_parameters)

            # filter by inputed parameters
            tracks = filter(lambda t: pa.filter_by_parameters(parameters, track, t), tracks)

            #todo blush up how to load tracks
            if len(tracks) <= 5:
                history = SessionManager.get_session(request, SessionManager.CRITICIZE_SESSION)
                conditions = pa.parameters_to_conditions(parameters)
                tracks = cls.get_tracks(conditions, tracks, history)

        if len(tracks) > 0 and track:
            evaluator = Track.make_evaluator(TrackCriticizePattern)
            evaluated = evaluator.calc_score(tracks, track)

            # to dictionary
            serialized_evaluated = map(lambda s: {"score": s.score, "item": s.item.to_dict(), "score_detail": s.score_detail}, evaluated)

            # store to session
            SessionManager.set_session(request, SessionManager.TRACK_SESSION, map(lambda s: s["item"], serialized_evaluated))
            SessionManager.add_session(request, SessionManager.CRITICIZE_SESSION, posted_parameters)

            if limit > 0:
                serialized_evaluated = serialized_evaluated[:limit]

            response = json.dumps(serialized_evaluated)

        return HttpResponse(response, content_type="application/json")

    @classmethod
    def get_tracks(cls, conditions, initial_tracks, history=[]):
        track = Track()
        tracks = initial_tracks
        trial_count = 0
        cond = conditions

        while trial_count < RecommendApi.TRACK_TRIAL_LIMIT and len(tracks) <= RecommendApi.TRACK_COUNT_BASE:
            try:
                # get tracks by criticizes
                if len(tracks) > 0:
                    cond["offset"] = len(tracks)

                new_tracks = track.find(cond)
                tracks += filter(lambda t: t.id not in [t.id for t in tracks], new_tracks)
            except HTTPError as ex:
                pass

            trial_count += 1
            sleep(0.5)

        tracks = tracks[:RecommendApi.TRACK_COUNT_BASE]

        return tracks

    @classmethod
    def get_criticize_pattern(cls, request):
        if request.method == "POST":
            track_id = request.POST.get(u"track_id")

            tracks = cls.__get_session_tracks(request)
            track = cls.__get_track(track_id, tracks)
            limit = 3   #todo receive it from parameter

            evaluator = Track.make_evaluator(TrackCriticizePattern)
            criticize_patterns = evaluator.make_pattern(tracks, track)

            questions = TrackCriticizePattern.patterns_to_questions(criticize_patterns, track, tracks)
            if len(questions) > limit:
                questions = random.sample(questions, limit)

            serialized_question = json.dumps(questions)
            return HttpResponse(serialized_question, content_type="application/json")
        else:
            raise Exception("you have to use POST method when access the get_criticize_pattern.")

    @classmethod
    def __get_session_tracks(cls, request):
        tracks = SessionManager.get_session(request, SessionManager.TRACK_SESSION)
        tracks = Track().load_dict(tracks)  # deserialization
        return tracks

    @classmethod
    def __get_track(cls, target_track_id, tracks):
        track = None
        track = next(iter(filter(lambda t: t.id == target_track_id, tracks)), None)
        if track is None:
            track = Track.find_by_id(target_track_id)

        return track


class SessionManager(object):
    CRITICIZE_SESSION = "CRITICIZE_STORE_KEY"
    TRACK_SESSION = "TRACK_STORE_KEY"
    SOUNDCLOUD_ACCESS_TOKEN = "SOUNDCLOUD_ACCESS_TOKEN"

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

    @classmethod
    def remove_session(cls, request, key):
        del request.session[key]


@ensure_csrf_cookie
def index(request):
    return render(request, "soundcloudapi/index.html")


def __make_authorize_client(request):
    client = soundcloud.Client(
        client_id=secret_settings.SOUND_CLOUD_ID,
        client_secret=secret_settings.SOUND_CLOUD_SECRET,
        redirect_uri="http://{0}/soundcloudapi/authorized".format(request.get_host())
    )
    return client


def require_auth(request):

    client = __make_authorize_client(request)
    return HttpResponseRedirect(client.authorize_url())


def authorized(request):
    client = __make_authorize_client(request)

    access_token = client.exchange_token(code=request.GET.get('code'))
    SessionManager.set_session(request, SessionManager.SOUNDCLOUD_ACCESS_TOKEN, access_token.obj)
    r = HttpResponse()
    r.write("<script>window.opener._authorized(); window.close();</script>")  # close the window for authorization
    return r


def is_connect(request):
    has_token = SessionManager.SOUNDCLOUD_ACCESS_TOKEN in request.session
    return HttpResponse(json.dumps(has_token), content_type="application/json")


def disconnect(request):
    SessionManager.remove_session(request, SessionManager.SOUNDCLOUD_ACCESS_TOKEN)
    return HttpResponse(json.dumps({}), content_type="application/json")


def make_playlist(request):
    result = {"result": False, "message": u""}

    if SessionManager.SOUNDCLOUD_ACCESS_TOKEN in request.session:
        token = SessionManager.get_session(request, SessionManager.SOUNDCLOUD_ACCESS_TOKEN)
        proxy = {}
        if secret_settings.HTTP_PROXY:
            proxy["http"] = secret_settings.HTTP_PROXY

        client = soundcloud.Client(access_token=token[u"access_token"])

        posted = json.loads(request.body)
        title = posted.get(u"title")
        sharing = posted.get(u"sharing")
        liked = posted.get(u"liked")

        try:
            if not title:
                raise Exception(u"title is missing.")

            if not sharing:
                raise Exception(u"sharing is missing.")

            if not liked or len(liked) == 0:
                raise Exception(u"liked tracks are missing.")
            else:
                liked = map(lambda t: dict(id=int(t)), liked)

            # Validation will be done by api (if error, cause exception)
            playlist = client.post("/playlists", playlist={
                "title": title,
                "sharing": sharing,
                "tracks": liked
            })

            # get url
            result["result"] = True
            result["message"] = playlist.permalink_url


        except Exception as ex:
            result["message"] = ex.message

    else:
        result["message"] = u"You have to login to sound cloud."

    return HttpResponse(json.dumps(result), content_type="application/json")
