import enum


class CriticizeDirection(enum.Enum):
    Up = "+"
    Around = "@"
    Down = "-"


class CriticizeTarget(object):

    def __init__(self, name, direction, value=None):
        self.name = name
        if isinstance(direction, CriticizeDirection):
            self.direction = direction
        else:
            self.direction = CriticizeDirection(str(direction))

        self.value = value
