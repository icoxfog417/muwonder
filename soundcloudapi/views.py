import json
from time import sleep

from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from urllib.error import HTTPError
from soundcloudapi.models import Track, User
from soundcloudapi.service import soundcloud_client
from soundcloudapi.models import TrackCriticizePattern, TrackCriticizeType, Parameter, ParameterAdapter


class RecommendApi(object):
    TRACK_COUNT_BASE = 100
    TRACK_TRIAL_LIMIT = 3

    def __init__(self):
        pass

    @classmethod
    def recommends(cls, request):
        tracks = []
        pa = ParameterAdapter()
        limit = 10  # todo:get limit by parameter
        response = []

        # get request parameters
        request_body = None
        if request.method == "GET":
            request_body = list(request.GET.dict().keys())[0]
        else:
            request_body = request.body.decode("utf-8")

        posted = json.loads(request_body)
        posted_parameters = {} if not "parameters" in posted else posted["parameters"]

        # process by methods
        if request.method == "GET":
            # initialize when get
            SessionManager.set_session(request, SessionManager.CRITICIZE_SESSION, [])
            SessionManager.set_session(request, SessionManager.TRACK_SESSION, [])

            parameters = pa.request_to_parameters(TrackCriticizeType.Parameter, None, posted_parameters)
            tracks = cls.get_scored_tracks(parameters, None, [])

        else:
            track_id = posted["track_id"]
            criticize_type = TrackCriticizeType(posted["criticize_type"])
            track = cls.__get_track(track_id, tracks)
            tracks = cls.__get_session_tracks(request)  # get from session

            parameters = pa.request_to_parameters(criticize_type, track, posted_parameters)
            history = cls.__get_session_history(request)

            # merge history and make parameter
            parameters = ParameterAdapter.merge_parameters(history + [parameters])

            if criticize_type == TrackCriticizeType.Like:
                tracks = cls.get_favorite_tracks(parameters, track, tracks)
            else:
                tracks = cls.get_scored_tracks(parameters, track, tracks)

        if len(tracks) > 0:
            # to dictionary
            serialized_evaluated = [{"score": s.score, "item": s.item.to_dict(), "score_detail": s.score_detail} for s in tracks]

            # store to session
            SessionManager.set_session(request, SessionManager.TRACK_SESSION, [s["item"] for s in serialized_evaluated])
            SessionManager.add_session(request, SessionManager.CRITICIZE_SESSION, [p.to_dict() for p in parameters])

            if limit > 0:
                serialized_evaluated = serialized_evaluated[:limit]

            response = serialized_evaluated

        return HttpResponse(json.dumps(response), content_type="application/json")

    @classmethod
    def get_scored_tracks(cls, parameters, track, initial_tracks):
        tracks = []
        trial_count = 0
        finder = Track()
        base_track = track
        pa = ParameterAdapter()
        conditions = pa.parameters_to_conditions(parameters)

        while trial_count < RecommendApi.TRACK_TRIAL_LIMIT and len(tracks) <= RecommendApi.TRACK_COUNT_BASE:
            try:
                # get tracks by criticizes
                if len(tracks) > 0:
                    conditions["offset"] = len(tracks)

                if trial_count == 0:
                    tracks += initial_tracks

                new_tracks = finder.find(conditions)
                tracks += list(filter(lambda t: t.id not in [t.id for t in tracks], new_tracks))

                # filter by inputed parameters
                if track:
                    tracks = list(filter(lambda t: pa.filter_by_parameters(parameters, track, t), tracks))

            except HTTPError as ex:
                    pass

            trial_count += 1
            sleep(0.5)

        scored = tracks
        if len(tracks) > 0:
            if track is None:
                base_track = tracks[0]

            evaluator = Track.make_evaluator(TrackCriticizePattern)
            scored = evaluator.calc_score(tracks, base_track)

        scored = scored[:RecommendApi.TRACK_COUNT_BASE]

        return scored

    @classmethod
    def get_favorite_tracks(cls, parameters, track, initial_tracks):
        if track is None:
            Exception("If getting favorite, you have to set track parameter")

        tracks = []
        favoriters = []
        trial_count = 0
        pa = ParameterAdapter()
        user_evaluator = User.make_evaluator()

        while trial_count < RecommendApi.TRACK_TRIAL_LIMIT and len(tracks) <= RecommendApi.TRACK_COUNT_BASE:
            try:
                # get tracks by criticizes
                if trial_count == 0:
                    favoriters = track.get_favoriters()
                    if len(favoriters) > 0:
                        favoriters = user_evaluator.calc_score(favoriters, favoriters[0])
                    else:
                        break

                if len(favoriters) > trial_count:
                    new_tracks = favoriters[trial_count].item.get_favorites()
                    tracks += list(filter(lambda t: t.id not in [t.id for t in tracks], new_tracks))
                    tracks = list(filter(lambda t: pa.filter_by_parameters(parameters, track, t), tracks))

            except HTTPError as ex:
                pass

            trial_count += 1
            sleep(0.5)

        scored = []
        if len(tracks) > 0:
            evaluator = Track.make_evaluator(TrackCriticizePattern)
            scored = evaluator.calc_score(tracks, track)
        else:
            scored = cls.get_scored_tracks(parameters, track, tracks)

        scored = scored[:RecommendApi.TRACK_COUNT_BASE]

        return scored

    @classmethod
    def get_criticize_pattern(cls, request):
        if request.method == "POST":
            posted = json.loads(request.body.decode("utf-8"))
            track_id = posted["track_id"]

            tracks = cls.__get_session_tracks(request)
            track = cls.__get_track(track_id, tracks)

            evaluator = Track.make_evaluator()
            criticize_patterns = evaluator.make_pattern(tracks, track)

            questions = TrackCriticizePattern.patterns_to_questions(criticize_patterns, track, tracks)
            serialized_question = json.dumps(questions)
            return HttpResponse(serialized_question, content_type="application/json")
        else:
            raise Exception("You have to use POST method when access the get_criticize_pattern.")

    @classmethod
    def __get_session_tracks(cls, request):
        tracks = SessionManager.get_session(request, SessionManager.TRACK_SESSION)
        tracks = Track().load_dict(tracks)  # deserialization
        return tracks

    @classmethod
    def __get_session_history(cls, request):
        parameters = SessionManager.get_session(request, SessionManager.CRITICIZE_SESSION)
        parameters = Parameter().load_dict(parameters)  # deserialization
        return parameters

    @classmethod
    def __get_track(cls, track_id, tracks):
        if not track_id:
            Exception("Track id is not defined")

        track = None
        track = next(iter(filter(lambda t: t.id == track_id, tracks)), None)
        if track is None:
            track = Track.find_by_id(track_id)

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


def require_auth(request):
    client = soundcloud_client.create_for_authorization(request.get_host())
    return HttpResponseRedirect(client.authorize_url())


def authorized(request):
    client = soundcloud_client.create_for_authorization(request.get_host())

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
    result = {"result": False, "message": ""}

    if SessionManager.SOUNDCLOUD_ACCESS_TOKEN in request.session:
        token = SessionManager.get_session(request, SessionManager.SOUNDCLOUD_ACCESS_TOKEN)
        client = soundcloud_client.create_by_token(token)

        posted = json.loads(request.body.decode("utf-8"))
        title = posted.get("title")
        sharing = posted.get("sharing")
        liked = posted.get("liked")

        try:
            if not title:
                raise Exception("title is missing.")

            if not sharing:
                raise Exception("sharing is missing.")

            if not liked or len(liked) == 0:
                raise Exception("liked tracks are missing.")
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
        result["message"] = "You have to login to sound cloud."

    return HttpResponse(json.dumps(result), content_type="application/json")
