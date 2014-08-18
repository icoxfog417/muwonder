from json_serialiable import JsonSerializable
from target_class import print_title, SerializableClass
import json
import unittest


class SerializeTestCase(unittest.TestCase):
    @print_title
    def test_json_is_valid(self):
        target = SerializableClass()
        json_str = target.to_json()

        deserializer = SerializableClass()
        deserialized = deserializer.load_json(json_str)

        self.assertEqual(json_str, deserialized.to_json())

    def __deserialize(self):
        target = SerializableClass()
        json_str = target.to_json()

        deserializer = SerializableClass()
        deserialized = deserializer.load_json(json_str)

        return deserialized
