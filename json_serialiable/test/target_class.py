from json_serialiable import JsonSerializable
from datetime import datetime


class SerializableClass(JsonSerializable):

    def __init__(self):
        super(SerializableClass, self).__init__()

        self.number = 100
        self.string = "XXX"

        self.__private = 10
        self.getter = lambda: self.__private

        self.list = [10, 11, 12]
        self.tuple = ("A", "B", "C")

        self.date = datetime.today()
        self.obj = SerialiableKeyValue("A", "100")
        self.obj_list = map(lambda key: SerialiableKeyValue(key, ord(key)), ("A", "B", "C"))
        self.nested_list = ["A", ["B", "C"]]
        self.nested_obj_list = [SerialiableKeyValue("A", 100), [SerialiableKeyValue("B", 200), SerialiableKeyValue("C", 300)]]


class SerialiableKeyValue(JsonSerializable):

    def __init__(self, key=None, value=None):
        super(SerialiableKeyValue, self).__init__()
        self.key = key
        self.value = value


def print_title(test_case):

    def wrapper(*args, **kwargs):
        print("@" + test_case.__name__ + "-------------------------------------------")
        return test_case(*args, **kwargs)

    return wrapper
