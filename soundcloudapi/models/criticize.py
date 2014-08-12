import enum
import copy
from datetime import datetime, timedelta
from knowbre import CriticizePattern, CriticizeItem, CriticizeDirection
from soundcloudapi.models import Track
import random


class CriticizeType(enum.Enum):
    Proposed = 0
    Input = 1
    Taste = 2


class Criticize(object):

    def __init__(self, track_id, criticize_type, value={}):
        self.track_id = track_id

        if isinstance(criticize_type, CriticizeType):
            self.criticize_type = criticize_type
        elif isinstance(criticize_type, int):
            self.criticize_type = CriticizeType(criticize_type)
        else:
            self.criticize_type = CriticizeType(int(criticize_type))

        self.value = value

    def get_track(self, track_id=None):
        tracks = []
        if track_id:
            tracks = Track().find({"ids": track_id})
        else:
            tracks = Track().find({"ids": self.track_id})

        if len(tracks) > 0:
            return tracks[0]
        else:
            return None

    def to_pattern(self):
        if self.criticize_type == CriticizeType.Proposed:
            cp = CriticizePattern(self.value)
            cp.pattern_text = self.customize_pattern_text(cp)
            return cp
        else:
            return None

    @classmethod
    def customize_pattern_text(cls, customize_pattern):
        text = customize_pattern.pattern_text
        if customize_pattern.is_positive():
            text = text.replace(u"genre score", u"loud genre")
            text = text.replace(u"elapsed", u"old")
        else:
            text = text.replace(u"genre score", u"calm genre")
            text = text.replace(u"elapsed", u"recent")
        return text

    def to_dict(self):
        target_track = None
        if not self.track_id:
            raise Exception("Target track-id is not set yet")
        else:
            target_track = self.get_track()
            if not target_track:
                raise Exception("Track " + self.track_id + " is not found ")

        conditions = {}
        if self.criticize_type == CriticizeType.Input:
            if "bpm" in self.value:
                conditions = self.__make_conditions(CriticizeItem.direction_around(self.value["bpm"]))

        elif self.criticize_type == CriticizeType.Proposed:
            criticize = CriticizePattern(pattern=self.value)
            items = {}
            for c in criticize.get_pattern_properties():
                if c in self.__get_criticizable():
                    target_value = getattr(target_track, c)
                    items.update({c: CriticizeItem.direction(criticize.is_positive(), target_value)})

            conditions = self.__make_conditions(**items)

        elif self.criticize_type == CriticizeType.Taste:
            items = {}
            for c in self.__get_criticizable():
                target_value = getattr(target_track, c)
                if c == "created_at":
                    continue
                elif c == "genre":
                    target_value = target_value.lower()

                items.update({c: CriticizeItem.direction_around(target_value)})

            conditions = self.__make_conditions(**items)

        return conditions

    def to_conditions(self):
        c_dict = self.to_dict()
        if "genre_score" in c_dict:
            genres = Track.get_genres()
            g_score = c_dict["genre_score"]
            # when condition, name is "genres"
            c_dict["genres"] = u",".join(sorted(genres, key=lambda k: abs(genres[k] - g_score))[:3])
            c_dict.pop("genre_score")

        if "genre" in c_dict:
            c_dict["genres"] = c_dict["genre"]
            c_dict.pop("genre")

        if self.criticize_type == CriticizeType.Proposed:
            c_dict = self.__set_default_conditions(c_dict)

        return c_dict

    @classmethod
    def get_default_conditions(cls):
        return cls.__set_default_conditions({})

    @classmethod
    def __set_default_conditions(cls, conditions):
        cond = copy.deepcopy(conditions)
        if not "created_at" in cond:
            base_date = datetime.now() - timedelta(days=365)
            cond["created_at"] = {"from": base_date.strftime("%Y-%m-%d %H:%M:%S")}
        if not "genres" in cond:
            random_genres = random.sample(Track.get_genres().keys(), 5)
            cond["genres"] = u",".join(random_genres)
        if not "filter" in cond:
            cond["filter"] = u"streamable"

        return cond

    @classmethod
    def __get_criticizable(cls):
        return ["bpm", "genre", "created_at"]

    @classmethod
    def __make_conditions(cls, bpm=None, genre=None, created_at=None):
        conditions = {}
        if bpm and bpm.value:
            if bpm.direction == CriticizeDirection.Up:
                conditions["bpm"] = {"from": str(bpm.value + 20)}
            elif bpm.direction == CriticizeDirection.Down:
                conditions["bpm"] = {"to": str(bpm.value - 20)}
            else:
                conditions["bpm"] = {"from": str(bpm.value - 20), "to": str(bpm.value + 20)}

        if genre and genre.value:
            conditions["genre"] = genre.value
            if Track.genre_to_score(genre.value):
                g_score = Track.genre_to_score(genre.value)
                if bpm.direction == CriticizeDirection.Up:
                    g_score += 0.1
                elif bpm.direction == CriticizeDirection.Down:
                    g_score -= 0.1

                conditions["genre_score"] = g_score

        if created_at and created_at.value:
            base_date = created_at.value
            if created_at.direction == CriticizeDirection.Up:
                base_date = base_date + timedelta(days=180)
            elif created_at.direction == CriticizeDirection.Down:
                base_date = base_date + timedelta(days=180)

            if base_date > datetime.now():
                base_date = datetime.now() - timedelta(days=90)

            conditions["created_at"] = {"from": base_date.strftime("%Y-%m-%d %H:%M:%S")}

        return conditions
