from knowbre import CriticizeItem, CriticizePattern, CriticizeDirection
from item_evaluator_test import print_title
import unittest


class CriticizeTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @print_title
    def test_criticize_pattern(self):
        cp = CriticizePattern("+:score, number")
        print(cp)
