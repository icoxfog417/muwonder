import enum
from datetime import datetime, timedelta
from knowbre import CriticizePattern, CriticizeDirection, vector_manager
from soundcloudapi.models import Track
import random


class TrackCriticizeType(enum.Enum):
    Pattern = 0
    Parameter = 1
    Like = 2


class TrackCriticize(object):

    def __init__(self, track_id, criticize_type, value={}, query=u""):
        self.track_id = track_id
        self._track = None
        self.query = query

        if isinstance(criticize_type, TrackCriticizeType):
            self.criticize_type = criticize_type
        elif isinstance(criticize_type, int):
            self.criticize_type = TrackCriticizeType(criticize_type)
        else:
            self.criticize_type = TrackCriticizeType(int(criticize_type))

        self.value = value

    def set_track(self, track):
        self.track_id = track.id
        self._track = track

    def get_track(self, track_id=None):
        track = None

        def get_track_by_id(t_id):
            tracks = Track().find({"ids": t_id})
            if len(tracks) > 0:
                return tracks[0]
            else:
                return None

        if track_id:
            track = get_track_by_id(track_id)
        elif self._track:
            track = self._track
        else:
            track = get_track_by_id(self.track_id)
            self._track = track  # cache the result

        return track

    def is_fit_criticize(self, target):
        base = self.get_track()
        if self.criticize_type == TrackCriticizeType.Pattern:
            cp = CriticizePattern(pattern=self.value)
            return cp.is_fit_pattern(base, target)
        else:
            params = self.make_parameters()
            result = True
            for key in params:
                target_value = vector_manager.to_value(target.__dict__[key])
                if params[key] is not None and target_value is not None and key in self.__get_comparable():
                    if not (self.__adjust(key, params[key], False) <= target_value <= self.__adjust(key, params[key], True)):
                        result = False

            return result

    @classmethod
    def __get_criticizable(cls):
        return ["bpm", "genre", "created_at"]

    @classmethod
    def __get_comparable(cls):
        return ["bpm", "genre_score", "created_at", "comment_count", "download_count", "playback_count", "favoritings_count"]

    def make_parameters(self):
        target_track = None
        if not self.track_id:
            raise Exception("Target track-id is not set yet")
        else:
            target_track = self.get_track()
            if not target_track:
                raise Exception("Track " + str(self.track_id) + " is not found ")

        parameters = {}
        if self.criticize_type == TrackCriticizeType.Parameter:
            if "bpm" in self.value:
                parameters["bpm"] = self.value["bpm"]

        elif self.criticize_type == TrackCriticizeType.Pattern:
            criticize = CriticizePattern(pattern=self.value)
            for c in criticize.get_targets():
                if c.name in self.__get_criticizable():
                    target_value = getattr(target_track, c.name)
                    parameters[c.name] = target_value

        elif self.criticize_type == TrackCriticizeType.Like:
            for c in self.__get_comparable():
                target_value = getattr(target_track, c)
                parameters[c] = vector_manager.to_value(target_value)

        if "genre" in parameters and Track.genre_to_score(parameters["genre"]):
            g_score = Track.genre_to_score(parameters["genre"])
            parameters["genre_score"] = g_score

        return parameters

    def make_conditions(self):
        parameters = self.make_parameters()
        default_condition = self.get_default_conditions()

        direction = CriticizeDirection.Around
        if self.criticize_type == TrackCriticizeType.Pattern:
            direction = TrackCriticizePattern(pattern=self.value).get_direction()

        c_dict = {}
        is_condition_set = False
        for key in self.__get_criticizable() + ["genre_score"]:
            if key in parameters and parameters[key] is not None:
                value = parameters[key]
                is_condition_set = True
                if key == "bpm":
                    value = int(value)
                    if direction == CriticizeDirection.Up:
                        c_dict[key] = {"from": self.__adjust(key, value, True)}
                    elif direction == CriticizeDirection.Down:
                        c_dict[key] = {"to": self.__adjust(key, value, False)}
                    else:
                        c_dict[key] = {"from": self.__adjust(key, value, False), "to": self.__adjust(key, value, True)}

                elif key == "genre":
                    c_dict[key] = value

                elif key == "genre_score":
                    if direction == CriticizeDirection.Up:
                        c_dict[key] = self.__adjust(key, value, True)
                    elif direction == CriticizeDirection.Down:
                        c_dict[key] = self.__adjust(key, value, False)
                    else:
                        c_dict[key] = value

                elif key == "created_at":
                    if direction == CriticizeDirection.Up:
                        value = self.__adjust(key, value, True)
                    elif direction == CriticizeDirection.Down:
                        value = self.__adjust(key, value, False)

                    c_dict[key] = {"from": value.strftime("%Y-%m-%d %H:%M:%S")}

        if self.query:
            is_condition_set = True
            c_dict["q"] = self.query

        if "genre_score" in c_dict:
            genres = Track.get_genres()
            g_score = c_dict["genre_score"]
            # when condition, name is "genres"
            c_dict["genres"] = u",".join(sorted(genres, key=lambda k: abs(genres[k] - g_score))[:3])
            c_dict.pop("genre_score")
        elif "genre" in c_dict:
            c_dict["genres"] = c_dict["genre"]

        if "genre" in c_dict:
            c_dict.pop("genre")

        if is_condition_set:
            c_dict["filter"] = default_condition["filter"]
        else:
            c_dict = default_condition

        return c_dict

    def __adjust(self, parameter_name, value, is_up):
        result = None
        if not value:
            return None

        if parameter_name == "bpm":
            if is_up:
                result = value + 20
            else:
                result = value - 20

        if parameter_name == "genre_score":
            if is_up:
                result = value + 0.1
            else:
                result = value - 0.1

        if parameter_name == "created_at":
            if is_up:
                result = value + timedelta(days=180)
            else:
                result = value - timedelta(days=180)

            if result > datetime.now():
                result = datetime.now() - timedelta(days=90)

        if parameter_name in ["comment_count", "download_count", "playback_count", "favoritings_count"]:
            if is_up:
                result = value * 1.5
            else:
                result = value * 0.5

        return result

    @classmethod
    def get_default_conditions(cls):
        default_condition = {}
        base_date = datetime.now() - timedelta(days=730)
        default_condition["created_at"] = {"from": base_date.strftime("%Y-%m-%d %H:%M:%S")}

        random_genres = random.sample(Track.get_genres().keys(), 5)
        default_condition["genres"] = u",".join(random_genres)

        default_condition["filter"] = u"streamable"

        return default_condition


class TrackCriticizePattern(CriticizePattern):

    def __init__(self, pattern="", score=0.0):
        super(TrackCriticizePattern, self).__init__(pattern, score)

    def make_pattern_text(self):
        text = super(TrackCriticizePattern, self).make_pattern_text()

        if self.is_positive():
            text = text.replace(u"genre score", u"loud genre")
            text = text.replace(u"elapsed", u"old")
        else:
            text = text.replace(u"genre score", u"calm genre")
            text = text.replace(u"elapsed", u"recent")

        return text
