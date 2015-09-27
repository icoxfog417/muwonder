# from django.db import models
from django.conf.urls.static import static
import re
from datetime import datetime
from knowbre.item_evaluator import ItemEvaluator, EvaluationType
from json_serializable import JsonSerializable
from soundcloudapi.service import soundcloud_client
from soundcloudapi.models import SoundCloudResource


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
        self.elapsed = lambda: - (datetime.now() - self.created_at).total_seconds() if self.created_at else None
        self.user_id = ""
        self.title = ""
        self.permalink_url = ""
        self.artwork_url = ""
        self.description = ""
        self.genre = ""
        self.genre_score = lambda: self.genre_to_score(self.genre + " " + self.tag_list)
        self.tag_list = ""
        self.tag_tokens = lambda: self.tag_list_to_tokens(self.tag_list)
        self.track_type = ""
        self.bpm = 0
        self.comment_count = 0
        self.download_count = 0
        self.playback_count = 0
        self.favoritings_count = 0

        self.__client = soundcloud_client.create()

        if item:
            self.set_param(item)

    def set_param(self, item):
        self.id = item.id
        self.user_id = item.user_id
        self.title = item.title
        self.permalink_url = item.permalink_url
        self.description = item.description
        self.genre = item.genre if item.genre else ""
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
        else:
            self.created_at = datetime.strptime(" ".join(item.created_at.split(" ")[0:2]), '%Y/%m/%d %H:%M:%S')
            if item.artwork_url:
                self.artwork_url = item.artwork_url
            elif "avatar_url" in item.user:
                self.artwork_url = item.user["avatar_url"]
            else:
                self.artwork_url = static("soundcloudapi/images/soundcloud_default.png")

    @classmethod
    def tag_list_to_tokens(cls, tag_list):
        p = re.compile(u'".+?"')
        double_quoted = p.findall(tag_list)
        exclude_double_quoted = tag_list
        for dq in double_quoted:
            exclude_double_quoted = exclude_double_quoted.replace(dq, "")

        tokens = exclude_double_quoted.split()
        tokens = filter(None, map(lambda t: t.strip(), tokens))
        if len(double_quoted) > 0:
            tokens += map(lambda t: t.replace(u'"', ""), double_quoted)

        return tokens

    @classmethod
    def make_evaluator(cls, history=None):
        from .track_criticize_pattern import TrackCriticizePattern
        evaluator = ItemEvaluator(TrackCriticizePattern)
        evaluator.set_rule("elapsed", EvaluationType.LessIsBetter)
        evaluator.set_rule("genre_score", EvaluationType.NearIsBetter)
        evaluator.set_rule("bpm", EvaluationType.NearIsBetter)
        evaluator.set_rule("comment_count", EvaluationType.MoreIsBetter)
        evaluator.set_rule("download_count", EvaluationType.MoreIsBetter)
        evaluator.set_rule("playback_count", EvaluationType.MoreIsBetter)
        evaluator.set_rule("favoritings_count", EvaluationType.MoreIsBetter)
        evaluator.set_rule("tag_tokens", EvaluationType.TextTokens)

        # set weight by history
        evaluator.set_weight("comment_count", 1.5)
        evaluator.set_weight("playback_count", 2)
        evaluator.set_weight("favoritings_count", 2)

        return evaluator

    def find(self, conditions):
        """
        recoomend the tracks by inputed parameters
        @conditions
        """

        find_condition = conditions

        if find_condition:
            tracks = self.__client.get("/tracks", **find_condition)
        else:
            tracks = self.__client.get("/tracks", {})

        track_items = map(lambda t: Track(SoundCloudResource(t)), tracks)
        return track_items

    @classmethod
    def find_by_id(cls, track_id):
        tracks = Track().find({"ids": track_id})
        if len(tracks) > 0:
            return tracks[0]
        else:
            return None

    def get_favoriters(self):
        """
        get recoomend the tracks by inputed parameters
        @conditions
        """

        users = self.__client.get("/tracks/{0}/favoriters".format(self.id))
        from .user import User
        user_items = map(lambda u: User(SoundCloudResource(u)), users)
        return user_items

    @classmethod
    def score_to_genre(cls, score):
        genres = cls.get_genres()
        return min(genres, key=lambda k: abs(genres[k] - score))

    @classmethod
    def score_to_genres(cls, score, count):
        genres = cls.get_genres()
        sorted_genre = sorted(genres.keys(), key=lambda k: abs(genres[k] - score))
        return sorted_genre[:count]

    @classmethod
    def genre_to_score(cls, genre):
        score = None
        genres = cls.get_genres()
        target_genre = genre.lower().strip()

        def get_score(word):
            s = None
            for w in [word, word.replace("-", " ")]:
                if word in genres:
                    s = genres[w]
                else:
                    hits = filter(lambda g: g.find(word) > -1, genres)
                    if len(hits) > 0:
                        s = genres[hits[0]]

                    rev_hits = filter(lambda g: word.find(g) > -1, genres)
                    if len(rev_hits) > 0:
                        s = genres[rev_hits[0]]
            return s

        if target_genre in genres:
            score = genres[target_genre]
        else:
            genre_words = target_genre.split(",")
            for genre_word in genre_words:
                score = get_score(genre_word.strip())
                if score:
                    break

        return score

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
            "dj": 0.45,
            "hardcore techno": 0.4,
            "techno": 0.39,
            "trance": 0.38,
            "minimal techno": 0.36,
            "tech house": 0.35,
            "remix": 0.33,
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
