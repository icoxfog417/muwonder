from __future__ import division
import unittest
from datetime import datetime
from math import pow
import knowbre.vector_utils as vector_manager
from knowbre.item_evaluator import ItemEvaluator, NotCalculatable


class EvaluateItem(object):
    """
    Class to test evaluating item.
    It models music track.
    """

    def __init__(self, item=None):
        self.bpm = 0
        self.reviews = 0
        self.release_date = datetime.now()
        self.elapsed = lambda: (datetime.now() - self.release_date).total_seconds() if self.release_date else None
        self.__private_val = 1
        self.tags = []
        if item:
            self.set_params(item.bpm, item.reviews, item.release_date)

    def set_params(self, bpm, reviews, release_date):
        self.bpm = bpm
        self.reviews = reviews
        self.release_date = release_date
        return self


def print_title(test_case):

    def wrapper(*args, **kwargs):
        print("@" + test_case.__name__ + "-------------------------------------------")
        return test_case(*args, **kwargs)

    return wrapper


class EvaluateFunctionTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @print_title
    def test_get_attributes(self):
        item = EvaluateItem()
        attributes = ItemEvaluator.get_attributes(item)
        for a in attributes:
            print a
        self.assertEquals(5, len(attributes))  # 4 is the number of attribute except private.

    @print_title
    def test_to_vector_primitive(self):
        data = self.__create_test_data()
        self.__assert_vector_integrity(data, "bpm")

    @print_title
    def test_to_vector_function(self):
        data = self.__create_test_data()
        self.__assert_vector_integrity(data, "elapsed")

    def __assert_vector_integrity(self, obj_list, target_attribute, is_print=True):
        attributes = vector_manager.to_vector(target_attribute, obj_list)
        self.assertEquals(len(obj_list), len(attributes))
        for index, value in enumerate(attributes):
            if is_print:
                print value
            self.assertEquals(vector_manager.to_value(getattr(obj_list[index], target_attribute)), value)

    @print_title
    def test_normalize(self):
        data = [1.1, 2.4, 3.2, 4.6, 5.8, 6.5, 7.9, 8.1, 9.1, 10, None]
        mean = 5.87
        max_value = max(filter(None, data))
        min_value = min(filter(None, data))
        calc_result = map(lambda v: float(v - mean) / (max_value - min_value), filter(None, data))

        calc_returned = ItemEvaluator.normalize(data)

        for index, value in enumerate(calc_result):
            self.assertLess(abs(calc_result[index] - calc_returned[index]), 1 / pow(10, 5))

    @print_title
    def test_calc_more_is_better(self):
        data = self.__create_test_data()

        values = vector_manager.to_vector("reviews", data)
        max_value = max(filter(None, values))
        min_value = min(filter(None, values))
        calc_result = map(lambda v: (v - min_value) / (max_value - min_value), filter(None, values))

        calc_returned = ItemEvaluator.calc_more_is_better("reviews", data)

        for index, value in enumerate(calc_result):
            self.assertLess(abs(calc_result[index] - calc_returned[index]), 1 / pow(10, 5))
            print(calc_result[index])

    @print_title
    def test_calc_less_is_better(self):
        data = self.__create_test_data()

        values = vector_manager.to_vector("elapsed", data)
        max_value = max(filter(None, values))
        min_value = min(filter(None, values))

        calc_result = map(lambda v: (max_value - v) / (max_value - min_value), filter(None, values))

        calc_returned = ItemEvaluator.calc_less_is_better("elapsed", data)

        for index, value in enumerate(calc_result):
            self.assertLess(abs(calc_result[index] - calc_returned[index]), 1 / pow(10, 5))
            print(calc_result[index])

    @print_title
    def test_calc_near_is_better(self):
        data = self.__create_test_data()

        values = vector_manager.to_vector("bpm", data)
        max_value = max(filter(None, values))
        min_value = min(filter(None, values))
        selected = EvaluateItem().set_params(100, 10, datetime(2010, 4, 1, 0, 0))
        calc_result = map(lambda v: 1 - abs(v - selected.bpm) / (max_value - min_value), filter(None, values))

        calc_returned = ItemEvaluator.calc_near_is_better("bpm", data, selected)

        for index, value in enumerate(calc_result):
            self.assertLess(abs(calc_result[index] - calc_returned[index]), 1 / pow(10, 5))
            print(calc_result[index])

    @print_title
    def test_calc_text_token_distance(self):
        item_count = 5
        test_items = map(lambda x: EvaluateItem(), range(item_count))

        for i in range(item_count):
            if i == 0:
                test_items[i].tags = ["folk", "Rock", "Folk Rock", "Indie"]
            elif i == 1:
                test_items[i].tags = ["rock"]
            elif i == 2:
                test_items[i].tags = ["rock", "alternative rock"]
            elif i == 3:
                test_items[i].tags = ["magnet", "rock", "melodious chorus"]
            elif i == 4:
                test_items[i].tags = ["Rock", "Creature", "3d", "Mashup"]

        distances = ItemEvaluator.calc_text_token_distance("tags", test_items, test_items[0])
        print(distances)

    @print_title
    def test_calc_near_is_better_exception(self):
        data = self.__create_test_data()
        selected = EvaluateItem().set_params(None, None, None)

        self.assertRaises(NotCalculatable, ItemEvaluator.calc_near_is_better, *("bpm", data, selected))

    def __create_test_data(self):
        t1 = EvaluateItem().set_params(110, 10, datetime(2010, 4, 1, 0, 0))
        t2 = EvaluateItem().set_params(80, 5, datetime(2011, 4, 1, 0, 0))
        t3 = EvaluateItem().set_params(100, 12, datetime(2013, 4, 1, 0, 0))
        t4 = EvaluateItem().set_params(130, 8, datetime(2014, 4, 1, 0, 0))
        t5 = EvaluateItem().set_params(90, 15, datetime(2012, 9, 1, 0, 0))
        t6 = EvaluateItem().set_params(None, None, None)

        return [t1, t2, t3, t4, t5, t6]

if __name__ == "__main__":
    unittest.main()