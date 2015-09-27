import unittest
from knowbre.criticize_pattern import CriticizePattern
from knowbre.tests.item_evaluator_test import print_title


class CriticizeTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @print_title
    def test_criticize_pattern(self):
        cp = CriticizePattern("+:score, number")
        print(cp)
