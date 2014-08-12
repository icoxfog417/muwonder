import json
import inspect
from datetime import datetime


class JsonSerializable(object):

    def __init__(self):
        self.__convert_rule = {}
        self.__convert_rule.update({"datetime": lambda v: v.strftime("%Y/%m/%d %H:%M:%S")})

    def to_dict(self):
        dictionalized = self.__make_attribute_dict()
        return dictionalized

    def to_json(self):
        return json.dumps(self.to_dict())

    def __make_attribute_dict(self):
        attributes = self.__get_class_attributes()
        attr_dict = {}
        for a in attributes:
            name = a[0]
            value = a[1]
            if isinstance(value, JsonSerializable):
                attr_dict[name] = value.__make_attribute_dict()
            if type(value).__name__ in self.__convert_rule:
                attr_dict[name] = self.__convert_rule[type(value).__name__](value)
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
