# from django.db import models
import soundcloud
import secret_settings
from datetime import datetime
from knowbre.item_evaluator import ItemEvaluator, EvaluationType
from soundcloudapi.models import JsonSerializable


# Create your models here.
class Track(JsonSerializable):
    """
    Represent Soundcloud's Track data
    """

    def __init__(self, item=None):
        """
        create __client by secret client key to access soundcloud
        """
        super(Track, self).__init__()

        self.id = ""
        self.created_at = datetime.now()
        self.elapsed = lambda: (datetime.now() - self.created_at).total_seconds() if self.created_at else None
        self.user_id = ""
        self.title = ""
        self.permalink_url = ""
        self.artwork_url = ""
        self.description = ""
        self.genre = ""
        self.genre_score = lambda: next(iter(filter(None, map(lambda v: self.genre_to_score(v), self.genre.split(",")))), None)
        self.tag_list = []
        self.track_type = ""
        self.bpm = 0
        self.comment_count = 0
        self.download_count = 0
        self.playback_count = 0
        self.favoritings_count = 0

        proxy = {}
        if secret_settings.HTTP_PROXY:
            proxy["http"] = secret_settings.HTTP_PROXY

        self.__client = soundcloud.Client(client_id=secret_settings.SOUND_CLOUD_ID, proxies=proxy)

        if item:
            self.set_param(item)

    def set_param(self, item):
        self.id = item.id
        self.user_id = item.user_id
        self.title = item.title
        self.permalink_url = item.permalink_url
        self.description = item.description
        self.tag_list = item.tag_list
        self.track_type = item.track_type
        self.bpm = item.bpm
        self.comment_count = item.comment_count
        self.download_count = item.download_count
        self.playback_count = item.playback_count
        self.favoritings_count = item.favoritings_count

        if isinstance(item, Track):
            self.created_at = item.created_at
            self.artwork_url = item.artwork_url
            self.genre = item.genre if item.genre else ""
        else:
            self.created_at = datetime.strptime(" ".join(item.created_at.split(" ")[0:2]), '%Y/%m/%d %H:%M:%S')
            if item.artwork_url:
                self.artwork_url = item.artwork_url.replace("-large", "-tiny")
            elif "avatar_url" in item.user:
                self.artwork_url = item.user["avatar_url"]
            self.genre = item.genre if item.genre else ""

    @classmethod
    def make_evaluator(cls, session=None):
        evaluator = ItemEvaluator()
        evaluator.set_rule("elapsed", EvaluationType.LessIsBetter)
        evaluator.set_rule("genre_score", EvaluationType.NearIsBetter)
        evaluator.set_rule("bpm", EvaluationType.NearIsBetter)
        evaluator.set_rule("comment_count", EvaluationType.MoreIsBetter)
        evaluator.set_rule("download_count", EvaluationType.MoreIsBetter)
        evaluator.set_rule("playback_count", EvaluationType.MoreIsBetter)
        evaluator.set_rule("favoritings_count", EvaluationType.MoreIsBetter)

        # set weight by session

        return evaluator

    def find(self, conditions):
        """
        recoomend the tracks by inputed parameters
        @conditions
        """

        tracks = self.__client.get("/tracks", **conditions)
        track_items = map(lambda t: Track(t), tracks)
        return track_items

    @classmethod
    def score_to_genre(cls, score):
        return min(cls.get_genres(), key=lambda v: abs(v[1] - score))

    @classmethod
    def genre_to_score(cls, genre):
        genres = cls.get_genres()
        if genre in genres:
            return genres[genre]
        else:
            return None

    @classmethod
    def get_genres(cls):
        genres = {
            "metal": 1,
            "disco": 0.95,
            "dance": 0.9,
            "hip hop": 0.85,
            "rap": 0.84,
            "progressive house": 0.8,
            "house": 0.77,
            "trap": 0.71,
            "trip hop": 0.7,
            "r&b": 0.65,
            "soul": 0.6,
            "latin": 0.55,
            "reggae": 0.5,
            "hardcore techno": 0.4,
            "techno": 0.39,
            "trance": 0.38,
            "minimal techno": 0.36,
            "tech House": 0.35,
            "electro": 0.31,
            "electronic": 0.3,
            "alternative rock": 0.2,
            "indie rock": 0.18,
            "punk": 0.15,
            "rock": 0.1,
            "pop": 0,
            "singer-songwriter": -0.1,
            "jazz": -0.15,
            "dubstep": -0.4,
            "deep house": -0.5,
            "bass": -0.6,
            "ambient": -0.65,
            "folk": -0.7,
            "country": -0.75,
            "piano": -0.9,
            "classical": -1
        }
        return genres
