from knowbre import vector_utils
from knowbre.criticize_target import CriticizeDirection, CriticizeTarget


class CriticizePattern(object):

    def __init__(self, pattern="", score=0.0):
        self.pattern = pattern
        self.score = score

    def is_positive(self):
        return self.pattern.split(":")[0] == "+"

    def get_direction(self):
        direction = CriticizeDirection(self.pattern.split(":")[0])
        return direction

    def get_targets(self):
        criticize = [CriticizeTarget(token.strip(), self.get_direction()) for token in self.pattern.split(":")[1].split(",")]
        return criticize

    def is_fit_pattern(self, base_item, target_item):
        is_fit = []
        if base_item is None or target_item is None:
            return False

        for p in self.get_targets():
            base_value = vector_utils.to_value(getattr(base_item, p.name))
            target_value = vector_utils.to_value(getattr(target_item, p.name))
            v = 0
            if target_value and base_value:
                if target_value > base_value:
                    v = 1
                elif target_value < base_value:
                    v = -1

            is_fit.append(v)

        if self.get_direction() == CriticizeDirection.Up and sum(is_fit) == len(is_fit):
            # pattern is positive, and exactly all pattern is True
            return True
        elif self.get_direction() == CriticizeDirection.Down and - sum(is_fit) == len(is_fit):
            # pattern is negative, and exactly all pattern is False
            return True
        elif self.get_direction() == CriticizeDirection.Around and sum(is_fit) == 0:
            # pattern is around, and exactly all pattern is equal
            return True
        else:
            return False

    def __str__(self):
        return self.make_pattern_text() + "(" + self.pattern + ")  " + str(self.score)

    def make_pattern_text(self):
        """
        Override this method to create text
        :return:
        """

        text = "Do you like "
        if self.is_positive():
            text += "more "
        else:
            text += "less "

        text += " and ".join(map(lambda p: p.name.replace("_", " "), self.get_targets()))
        text += "?"

        return text

    def to_dict(self):
        return {
            "pattern": self.pattern,
            "text": self.make_pattern_text()
        }
