import inspect


def to_value(prop):
    if inspect.isfunction(prop):
        return prop()
    else:
        return prop


def to_vector(attr_name, item_list):
    def attribute_to_value(obj, name):
        if obj:
            v = getattr(obj, name)
            return to_value(v)
        else:
            return None

    attr_vector = map(lambda el: attribute_to_value(el, attr_name), item_list)
    return attr_vector
