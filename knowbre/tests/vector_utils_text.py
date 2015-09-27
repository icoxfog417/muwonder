from knowbre import vector_utils
import math
import unittest


class VectorUtilTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_classify_text_token(self):
        classified = vector_utils.make_text_clusters([["AAA", "BBB", "CCC"], ["AAA", "ZZZ"], ["aaa", "BBB", "CCC"]])
        print(classified)

    def test_calc_vector_distance(self):
        distance = vector_utils.calc_vector_distance([0, 0], [1, 1])
        self.assertLess(math.sqrt(2) - distance, math.pow(0.1, 10))

        distance = vector_utils.calc_vector_distance([1, 1], [2, 1 + math.sqrt(3)])
        self.assertLess(2 - distance, math.pow(0.1, 10))

    def test_get_item_in_vector(self):
        v = ["a", "b", "c", "d"]
        result = vector_utils.get_item_in_vector(v, [1, 0, 1, 0])
        print(result)
        self.assertEqual(result, ["a", "c"])
