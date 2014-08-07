import json
import inspect


class JsonSerializable(object):

    def __init__(self):
        pass

    def to_json(self):
        dictionalized = self.__make_attribute_dict()
        return json.dump(dictionalized)

    @classmethod
    def to_json_array(cls, json_serializable_array):
        dictionalized_array = map(lambda js: js.__make_attribute_dict(), json_serializable_array)
        return json.dump(dictionalized_array)

    def __make_attribute_dict(self):
        attributes = self.__get_class_attributes()
        attr_dict = {}
        for a in attributes:
            name = a[0]
            value = a[1]
            if isinstance(value, JsonSerializable):
                attr_dict[name] = value.__make_attribute_dict()
            else:
                attr_dict[name] = self.__attribute_to_value(value)

        return attr_dict

    def __get_class_attributes(self):
        attributes = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        attributes.extend(inspect.getmembers(self, lambda a: inspect.isfunction(a)))
        # exclude private attribute
        return filter(lambda a: not(a[0].startswith("_")), attributes)

    @classmethod
    def __attribute_to_value(cls, attribute):
        if inspect.isfunction(attribute):
            return attribute()
        else:
            return attribute
