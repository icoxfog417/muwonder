from __future__ import division
from item_evaluator_test import EvaluateItem, print_title
from knowbre import ItemEvaluator, CriticizePattern
import unittest
from datetime import datetime, timedelta
import random
import math


class EvaluationTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @print_title
    def test_calc_score(self):
        data = self.__create_test_data()
        selected = EvaluateItem().set_params(100, 10, datetime(2010, 4, 1, 0, 0))

        evaluator = self.__get_ruled_evaluator()
        scores = evaluator.calc_score(data, selected)
        for scored in scores:
            print "score= bpm {0}, reviews {1}, elapsed {2} -> {3}.".format(scored.item.bpm, scored.item.reviews, scored.item.elapsed(), scored.score)
            print scored.score_detail

    @print_title
    def test_calc_score_with_weight(self):
        data = self.__create_test_data()
        selected = EvaluateItem().set_params(100, 10, datetime(2010, 4, 1, 0, 0))

        evaluator = self.__get_ruled_evaluator()
        evaluator.set_weight({"bpm": 1.5, "reviews": 0.5})
        scores = evaluator.calc_score(data, selected)

        default_scores = self.__get_ruled_evaluator().calc_score(data, selected)
        for index, scored in enumerate(scores):
            self.assertLess(
                abs(default_scores[index].score_detail["bpm"] * 1.5 + default_scores[index].score_detail["reviews"] * 0.5 + default_scores[index].score_detail["elapsed"]
                    - scored.score), 1 / pow(10, 5))
            print "score= bpm {0}, reviews {1}, elapsed {2} -> {3}.".format(scored.item.bpm, scored.item.reviews, scored.item.elapsed(), scored.score)

    @print_title
    def test_calc_score_with_none(self):
        data = self.__create_test_data()
        selected = EvaluateItem().set_params(None, 10, datetime(2010, 4, 1, 0, 0))

        evaluator = self.__get_ruled_evaluator()
        scores = evaluator.calc_score(data, selected)
        for scored in scores:
            print "score= bpm {0}, reviews {1}, elapsed {2} -> {3}.".format(scored.item.bpm, scored.item.reviews, scored.item.elapsed(), scored.score)

    def __get_ruled_evaluator(self):
        evaluator = ItemEvaluator()
        evaluator.set_rule("bpm", ItemEvaluator.calc_near_is_better)
        evaluator.set_rule("reviews", ItemEvaluator.calc_more_is_better)
        evaluator.set_rule("elapsed", ItemEvaluator.calc_less_is_better)
        return evaluator

    @print_title
    def test_make_pattern(self):
        data = self.__create_test_data()
        selected = EvaluateItem().set_params(100, 10, datetime(2013, 4, 1, 0, 0))

        evaluator = ItemEvaluator()
        evaluator.set_rule("bpm", ItemEvaluator.calc_near_is_better)
        evaluator.set_rule("reviews", ItemEvaluator.calc_more_is_better)
        evaluator.set_rule("elapsed", ItemEvaluator.calc_less_is_better)

        patterns = evaluator.make_pattern(data, selected)
        for p in patterns:
            print p
            self.assertLess(abs(p.score - self.__calculate_pattern_percentage(p, selected, data)), 1 / pow(10, 5))

    def __calculate_pattern_percentage(self, pattern, selected, test_cases):
        total = len(test_cases)
        fit_count = 0
        for item in test_cases:
            if pattern.is_fit_pattern(selected, item):
                fit_count += 1

        # divide on python3 feature
        return fit_count / total

    def __create_test_data(self):
        t1 = EvaluateItem().set_params(110, 10, datetime(2010, 4, 1, 0, 0))
        t2 = EvaluateItem().set_params(80, 5, datetime(2011, 4, 1, 0, 0))
        t3 = EvaluateItem().set_params(101, 12, datetime(2013, 4, 1, 0, 0))
        t4 = EvaluateItem().set_params(130, 8, datetime(2014, 4, 1, 0, 0))
        t5 = EvaluateItem().set_params(90, 15, datetime(2012, 9, 1, 0, 0))
        t6 = EvaluateItem().set_params(None, None, None)

        return [t1, t2, t3, t4, t5, t6]


    @print_title
    def test_criticize(self):
        evaluator = self.__get_ruled_evaluator()
        bpm_median = 100
        review_median = 10
        release_date_median = datetime(2013, 4, 1, 0, 0)

        datas = []
        for index in range(200):
            rand = random.random() - 0.5
            datas.append(EvaluateItem().set_params(
                bpm_median + math.floor(rand * 20),
                review_median + math.floor(rand * 10),
                release_date_median + timedelta(days=math.floor(rand * 365))
            ))

        item_space = map(lambda s: s.item, evaluator.calc_score(datas))
        selected = datas[0]
        pattern = None

        for i in range(5):
            length = len(item_space)
            if length == 0:
                break

            # user select from proposed items
            user_selected_at = int(math.floor(random.random() * length))
            selected = item_space[user_selected_at]

            # make criticize pattern by selected item
            patterns = evaluator.make_pattern(datas, selected)
            user_criticized_by = int(math.floor(random.random() * len(patterns)))

            # and user choose some criticize that proposed
            pattern = patterns[user_criticized_by]

            # update item space by criticize

            item_space = filter(None, map(lambda item: item if pattern.is_fit_pattern(selected, item) else None, item_space))

            print "user selected item at {0}/{1}, and criticized by {2}. then, item'count became {3} to {4}.".format(
                user_selected_at, length,  pattern.pattern, length, len(item_space))

            self.assertLess(len(item_space), length)

if __name__ == "__main__":
    unittest.main()
