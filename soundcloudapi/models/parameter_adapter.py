from datetime import datetime, timedelta
from knowbre import CriticizePattern, CriticizeDirection, vector_utils
from soundcloudapi.models import Track, TrackCriticizeType
import random


class ParameterAdapter(object):

    def request_to_parameters(self, criticize_type, track, request_parameters):
        if not track:
            raise Exception("Target track is None")

        parameters = {}
        if criticize_type == TrackCriticizeType.Parameter:
            if "bpm" in request_parameters:
                parameters["bpm"] = request_parameters["bpm"]

        elif criticize_type == TrackCriticizeType.Pattern:
            pattern = request_parameters["pattern"]
            criticize = CriticizePattern(pattern=pattern)
            parameters["pattern"] = pattern
            for c in criticize.get_targets():
                parameters[c.name] = vector_utils.to_value(getattr(track, c.name))

        elif criticize_type == TrackCriticizeType.Like:
            for c in self.__get_criticizables():
                parameters[c] = vector_utils.to_value(getattr(track, c))

        if "q" in request_parameters and request_parameters["q"]:
            parameters["q"] = request_parameters["q"]

        if "genre" in parameters and not "genre_score" in parameters:
            if Track.genre_to_score(parameters["genre"]):
                g_score = Track.genre_to_score(parameters["genre"])
                parameters["genre_score"] = g_score

        return parameters

    def track_to_parameters(self, track):
        return self.request_to_parameters(TrackCriticizeType.Like, track, {})

    def filter_by_parameters(self, parameters, base_track, target_track):
        if "pattern" in parameters:
            cp = CriticizePattern(pattern=parameters["pattern"])
            return cp.is_fit_pattern(base_track, target_track)
        else:
            return self.is_fit_track(base_track, target_track)

    def is_fit_track(self, base_track, target_track):
        result = True
        parameters = self.track_to_parameters(base_track)
        for key in parameters:
            target_value = vector_utils.to_value(target_track.__dict__[key])
            if parameters[key] is not None and target_value is not None:
                compare_value = self.adjust_parameter(key, parameters[key], False)
                if compare_value and not (compare_value <= target_value <= self.adjust_parameter(key, parameters[key], True)):
                    result = False

            return result

    def request_to_conditions(self, criticize_type, track, request_parameters):
        parameters = self.request_to_parameters(criticize_type, track, request_parameters)
        direction = CriticizeDirection.Around
        if criticize_type == TrackCriticizeType.Pattern:
            from .track_criticize_pattern import TrackCriticizePattern
            direction = TrackCriticizePattern(pattern=request_parameters["pattern"]).get_direction()

        return self.parameters_to_conditions(parameters, direction)

    def parameters_to_conditions(self, parameters, direction=CriticizeDirection.Around):
        default_condition = self.get_default_conditions()

        c_dict = {}
        is_condition_set = False
        for key in self.__get_conditionables():
            if key in parameters and parameters[key] is not None:
                value = parameters[key]
                is_condition_set = True
                if key == "bpm":
                    value = int(value)
                    if direction == CriticizeDirection.Up:
                        c_dict[key] = {"from": self.adjust_parameter(key, value, True)}
                    elif direction == CriticizeDirection.Down:
                        c_dict[key] = {"to": self.adjust_parameter(key, value, False)}
                    else:
                        c_dict[key] = {"from": self.adjust_parameter(key, value, False),
                                       "to": self.adjust_parameter(key, value, True)}

                elif key == "genre_score":
                    if direction == CriticizeDirection.Around:
                        c_dict[key] = value
                    else:
                        c_dict[key] = self.adjust_parameter(key, value, direction == CriticizeDirection.Up)

                elif key == "created_at":
                    value = self.adjust_parameter(key, value, direction == CriticizeDirection.Up)
                    c_dict[key] = {"from": value.strftime("%Y-%m-%d %H:%M:%S")}

                else:
                    c_dict[key] = value

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

    @classmethod
    def get_default_conditions(cls):
        default_condition = {}
        base_date = datetime.now() - timedelta(days=730)
        default_condition["created_at"] = {"from": base_date.strftime("%Y-%m-%d %H:%M:%S")}

        random_genres = random.sample(Track.get_genres().keys(), 5)
        default_condition["genres"] = u",".join(random_genres)

        default_condition["filter"] = u"streamable"

        return default_condition

    @classmethod
    def adjust_parameter(cls, parameter_name, value, is_up):
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
    def __get_criticizables(cls):
        return ["bpm", "genre", "genre_score", "created_at", "comment_count", "download_count", "playback_count", "favoritings_count"]

    @classmethod
    def __get_conditionables(cls):
        return ["q", "bpm", "genre", "genre_score", "created_at"]


