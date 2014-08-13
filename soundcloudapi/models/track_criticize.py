import enum
from datetime import datetime, timedelta
from knowbre import CriticizePattern, CriticizeDirection
from soundcloudapi.models import Track
import random


class TrackCriticizeType(enum.Enum):
    Pattern = 0
    Parameter = 1
    Like = 2


class TrackCriticize(object):

    def __init__(self, track_id, criticize_type, values={}):
        self.track_id = track_id
        self._track = None

        if isinstance(criticize_type, TrackCriticizeType):
            self.criticize_type = criticize_type
        elif isinstance(criticize_type, int):
            self.criticize_type = TrackCriticizeType(criticize_type)
        else:
            self.criticize_type = TrackCriticizeType(int(criticize_type))

        self.values = values

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

    @classmethod
    def __get_criticizable(cls):
        return ["bpm", "genre", "created_at"]

    def make_parameters(self):
        target_track = None
        if not self.track_id:
            raise Exception("Target track-id is not set yet")
        else:
            target_track = self.get_track()
            if not target_track:
                raise Exception("Track " + self.track_id + " is not found ")

        parameters = {}
        if self.criticize_type == TrackCriticizeType.Parameter:
            if "bpm" in self.values:
                parameters["bpm"] = self.values["bpm"]

        elif self.criticize_type == TrackCriticizeType.Pattern:
            criticize = CriticizePattern(pattern=self.values)
            for c in criticize.get_targets():
                if c.name in self.__get_criticizable():
                    target_value = getattr(target_track, c.name)
                    parameters[c.name] = target_value

        elif self.criticize_type == TrackCriticizeType.Like:
            for c in self.__get_criticizable():
                target_value = getattr(target_track, c)
                parameters[c] = target_value

        return parameters

    def adjust_parameter(self, direction, bpm=None, genre=None, created_at=None):
        adjusted = {}
        if bpm:
            if direction == CriticizeDirection.Up:
                adjusted["bpm"] = {"from": str(bpm + 20)}
            elif direction == CriticizeDirection.Down:
                adjusted["bpm"] = {"to": str(bpm - 20)}
            else:
                adjusted["bpm"] = {"from": str(bpm - 20), "to": str(bpm + 20)}

        if genre:
            adjusted["genre"] = genre
            if Track.genre_to_score(genre):
                g_score = Track.genre_to_score(genre)
                if direction == CriticizeDirection.Up:
                    g_score += 0.1
                elif direction == CriticizeDirection.Down:
                    g_score -= 0.1

                adjusted["genre_score"] = g_score

        if created_at:
            base_date = created_at
            if direction == CriticizeDirection.Up:
                base_date = base_date + timedelta(days=180)
            elif direction == CriticizeDirection.Down:
                base_date = base_date + timedelta(days=180)

            if base_date > datetime.now():
                base_date = datetime.now() - timedelta(days=90)

            adjusted["created_at"] = {"from": base_date.strftime("%Y-%m-%d %H:%M:%S")}

        return adjusted

    def to_conditions(self):
        parameters = self.make_parameters()
        direction = CriticizeDirection.Around
        if self.criticize_type == TrackCriticizeType.Pattern:
            direction = TrackCriticizePattern(pattern=self.values).get_direction()

        c_dict = self.adjust_parameter(direction, **parameters)
        default_condition = self.get_default_conditions()

        if "genre_score" in c_dict:
            genres = Track.get_genres()
            g_score = c_dict["genre_score"]
            # when condition, name is "genres"
            c_dict["genres"] = u",".join(sorted(genres, key=lambda k: abs(genres[k] - g_score))[:3])
            c_dict.pop("genre_score")

        if "genre" in c_dict:
            c_dict["genres"] = c_dict["genre"]
            c_dict.pop("genre")

        c_dict["filter"] = default_condition["filter"]

        return c_dict

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
