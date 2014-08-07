import enum
import vector_manager


class CriticizePattern(object):

    def __init__(self, pattern="", score=0.0):
        self.pattern = pattern
        self.score = score
        self.get_pattern_text = lambda p: ""

    def is_positive(self):
        return self.pattern.split(":")[0] == "+"

    def get_pattern_properties(self):
        return self.pattern.split(":")[1].split(",")

    def is_fit_pattern(self, base_item, target_item):
        is_fit = []
        for p in self.get_pattern_properties():
            base_value = vector_manager.to_value(getattr(base_item, p))
            target_value = vector_manager.to_value(getattr(target_item, p))
            if target_value > base_value:
                is_fit.append(1)
            elif target_value < base_value:
                is_fit.append(-1)
            else:
                is_fit.append(0)

        if self.is_positive() and sum(is_fit) == len(is_fit):
            # pattern is positive, and exactlly all pattern is True
            return True
        elif not self.is_positive() and - sum(is_fit) == len(is_fit):
            # pattern is negative, and exactlly all pattern is False
            return True
        else:
            return False

    def __str__(self):
        return self.get_pattern_text(self) + "(" + self.pattern + ")  " + str(self.score)

    def to_dict(self):
        return {
            "pattern": self.pattern,
            "text": self.get_pattern_text(self)
        }


class CriticizeDirection(enum.Enum):
    Up = 1
    Around = 0
    Down = -1


class CriticizeItem(object):

    def __init__(self, direction, value):
        self.direction = direction
        self.value = value

    @classmethod
    def direction(cls, is_up, value):
        if is_up:
            return CriticizeItem(CriticizeDirection.Up, value)
        else:
            return CriticizeItem(CriticizeDirection.Down, value)

    @classmethod
    def direction_up(cls, value):
        return CriticizeItem(CriticizeDirection.Up, value)

    @classmethod
    def direction_around(cls, value):
        return CriticizeItem(CriticizeDirection.Around, value)

    @classmethod
    def direction_down(cls, value):
        return CriticizeItem(CriticizeDirection.Down, value)

