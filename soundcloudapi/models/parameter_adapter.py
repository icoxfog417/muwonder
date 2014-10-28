import re
import random
from datetime import datetime, timedelta
import math
from knowbre import CriticizePattern, CriticizeDirection, vector_utils
from soundcloudapi.models import Track, TrackCriticizeType
from json_serialiable import JsonSerializable
from collections import defaultdict


class Parameter(JsonSerializable):

    def __init__(self, name="", value="", direction=CriticizeDirection.Around):
        super(Parameter, self).__init__()
        self.name = name
        self.value = value
        self.direction = direction

        def convert_if_dateformat(type, attr_value):
            if isinstance(attr_value, str) or isinstance(attr_value, unicode):
                m = re.search("\d{4}/\d{1,2}/\d{1,2}\s\d{1,2}\:\d{1,2}\:\d{1,2}", attr_value)
                if m is not None:
                    return datetime.strptime(attr_value, "%Y/%m/%d %H:%M:%S")
                else:
                    return attr_value
            else:
                return attr_value

        self.set_deserialize_rule({unicode: convert_if_dateformat})
        self.set_deserialize_rule({str: convert_if_dateformat})

    @classmethod
    def find(cls, name, parameter_array):
        items = filter(lambda p: p.name == name, parameter_array)
        return items

    @classmethod
    def first_or_default(cls, name, parameter_array, default=None):
        items = cls.find(name, parameter_array)
        if len(items) > 0:
            return items[0]
        else:
            return default

    def __str__(self):
        return u"{0}:{1}->{2}".format(self.direction, self.name, self.value)


class ParameterAdapter(object):

    def request_to_parameters(self, criticize_type, track, request_parameters):
        if criticize_type != TrackCriticizeType.Parameter and not track:
            raise Exception("Target track is None")

        parameters = []
        if criticize_type == TrackCriticizeType.Parameter:
            if "bpm" in request_parameters:
                parameters.append(Parameter("bpm", request_parameters["bpm"]))

        elif criticize_type == TrackCriticizeType.Pattern:
            criticize = CriticizePattern(pattern=request_parameters["pattern"])
            direction = criticize.get_direction()
            parameters.append(Parameter("pattern", criticize.pattern))
            for c in criticize.get_targets():
                parameters.append(Parameter(c.name, vector_utils.to_value(getattr(track, c.name)), direction))

        elif criticize_type == TrackCriticizeType.Like:
            for c in self.__get_criticizables():
                parameters.append(Parameter(c, vector_utils.to_value(getattr(track, c))))

        if "q" in request_parameters and request_parameters["q"]:
            parameters.append(Parameter("q", request_parameters["q"]))

        if Parameter.first_or_default("genre", parameters) and not Parameter.first_or_default("genre_score", parameters):
            genre = Parameter.first_or_default("genre", parameters)
            if Track.genre_to_score(genre):
                g_score = Track.genre_to_score(genre)
                parameters.append(Parameter("genre_score", g_score))

        return parameters

    def track_to_parameters(self, track):
        return self.request_to_parameters(TrackCriticizeType.Like, track, {})

    def filter_by_parameters(self, parameters, base_track, target_track):
        pattern = filter(lambda p: p.name == "pattern", parameters)
        if len(pattern) > 0:
            cp = CriticizePattern(pattern[0].value)
            return cp.is_fit_pattern(base_track, target_track)
        else:
            return self.is_fit_track(base_track, target_track)

    def is_fit_track(self, base_track, target_track):
        result = True
        parameters = self.track_to_parameters(base_track)
        for p in parameters:
            key = p.name
            target_value = vector_utils.to_value(target_track.__dict__[key])
            if not self.is_none_or_empty(p.value) and not self.is_none_or_empty(target_value):
                compare_value = self.adjust_parameter(key, p.value, False)
                if compare_value and not (compare_value <= target_value <= self.adjust_parameter(key, p.value, True)):
                    result = False

        return result

    @classmethod
    def is_none_or_empty(cls, value):
        if value is None or value == "" or value == u"":
            return True
        else:
            return False

    @classmethod
    def merge_parameters(cls, parameters_list):
        key_dict = defaultdict(list)
        for parameters in parameters_list:
            for p in parameters:
                key_dict[p.name].append(p)

        merged = []
        for key in key_dict:
            parameters = key_dict[key]
            if len(parameters) == 1:
                merged.append(parameters[0])
            else:
                d = parameters[-1].direction
                targets = [p.value for p in parameters if p.value is not None and p.direction == d]
                if len(targets) == 0:
                    continue

                dummy_value = cls.adjust_parameter(key, targets[0], False)
                is_calculatable = dummy_value is not None and not isinstance(dummy_value, datetime)
                v = None
                if is_calculatable:
                    if d == CriticizeDirection.Around:
                        v = reduce(lambda x, y: x+y, targets) / float(len(targets))
                    elif d == CriticizeDirection.Up:
                        v = max(targets)
                    elif d == CriticizeDirection.Down:
                        v = min(targets)
                else:
                    for i in reversed(range(len(targets))):
                        if targets[i]:
                            v = targets[i]
                            break

                merged.append(Parameter(key, v, d))

        return merged

    def request_to_conditions(self, criticize_type, track, request_parameters):
        parameters = self.request_to_parameters(criticize_type, track, request_parameters)
        return self.parameters_to_conditions(parameters)

    def parameters_to_conditions(self, parameters):
        default_condition = self.get_default_conditions()

        c_dict = {}
        is_condition_set = False
        for key in self.__get_conditionables():
            p = Parameter.first_or_default(key, parameters)
            if p is not None and p.value is not None:
                is_condition_set = True
                if key == "bpm":
                    value = int(p.value)
                    if p.direction == CriticizeDirection.Up:
                        c_dict[key] = {"from": self.adjust_parameter(key, value, True)}
                    elif p.direction == CriticizeDirection.Down:
                        c_dict[key] = {"to": self.adjust_parameter(key, value, False)}
                    else:
                        c_dict[key] = {"from": self.adjust_parameter(key, value, False),
                                       "to": self.adjust_parameter(key, value, True)}

                elif key == "genre_score":
                    if p.direction == CriticizeDirection.Around:
                        c_dict[key] = p.value
                    else:
                        c_dict[key] = self.adjust_parameter(key, p.value, p.direction == CriticizeDirection.Up)

                elif key == "created_at":
                    value = self.adjust_parameter(key, p.value, p.direction == CriticizeDirection.Up)
                    c_dict[key] = {"from": value.strftime("%Y-%m-%d %H:%M:%S")}

                else:
                    c_dict[key] = p.value

        if "genre_score" in c_dict:
            genre = Track.score_to_genre(c_dict["genre_score"])
            c_dict["genres"] = genre
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

    @classmethod
    def get_default_conditions(cls):
        default_condition = {}
        base_date = datetime.now() - timedelta(days=730)
        default_condition["created_at"] = {"from": base_date.strftime("%Y-%m-%d %H:%M:%S")}

        random_score = random.uniform(-1, 1)
        random_genres = Track.score_to_genres(random_score, 1)
        default_condition["genres"] = u",".join(random_genres)

        default_condition["filter"] = u"streamable"

        return default_condition

    @classmethod
    def adjust_parameter(cls, parameter_name, value, is_up):
        result = None
        if value is None:
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
                result = value + timedelta(days=365)
            else:
                result = value - timedelta(days=365)

            if result > datetime.now():
                if is_up:
                    result = datetime.now()
                else:
                    result = datetime.now() - timedelta(days=365)

        if parameter_name in ["playback_count", "favoritings_count"]:
            if is_up:
                result = math.exp(math.log(value) * 1.2)
            else:
                result = math.exp(math.log(value) * 0.8)

        return result

    @classmethod
    def __get_criticizables(cls):
        # not use comment_count and download_count. because commentable/downloadable track is there.
        return ["bpm", "genre", "genre_score", "created_at", "playback_count", "favoritings_count"]

    @classmethod
    def __get_conditionables(cls):
        return ["q", "bpm", "genre", "genre_score", "created_at"]
