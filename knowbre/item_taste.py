import enum


class ItemTaste(enum.Enum):
    """
    Define the item's type of taste.
    """

    # More is better : it is like spec. Higher spec is more preferred
    MIB = 1

    # Less is better : it is like price. Lower price is more preferred
    LIB = -1

    # Near is better : it is like color. User selected color is more preferred than other one.
    NIB = 0
