# -*- coding: utf-8 -*-
from __future__ import division
import inspect
import itertools
import enum
from collections import Counter
import vector_manager
from criticize_pattern import CriticizePattern


class EvaluationType(enum.Enum):
    MoreIsBetter = 0
    LessIsBetter = 1
    NearIsBetter = 2


class ItemEvaluator(object):

    def __init__(self):
        self.__rules = {}
        self.__weights = {}

    def get_rules(self):
        return self.__rules

    def get_weights(self):
        return self.__rules

    def set_rule(self, key_or_dict, rule=None):
        if isinstance(key_or_dict, dict) and not rule:
            self.__rules.update(key_or_dict)
        elif isinstance(rule, EvaluationType):
            if rule == EvaluationType.MoreIsBetter:
                self.__rules[key_or_dict] = self.calc_more_is_better
            elif rule == EvaluationType.LessIsBetter:
                self.__rules[key_or_dict] = self.calc_less_is_better
            elif rule == EvaluationType.NearIsBetter:
                self.__rules[key_or_dict] = self.calc_near_is_better
        else:
            self.__rules[key_or_dict] = rule

    def set_weight(self, key_or_dict, weight=None):
        if isinstance(key_or_dict, dict) and not weight:
            self.__weights.update(key_or_dict)
        else:
            self.__weights[key_or_dict] = weight

    @classmethod
    def __normalize(cls, values, normalize_value_type="", prop=None):
        normalized = []
        if len(filter(None, values)) == 0:
            return map(lambda nn: None, values)

        value_max = max(filter(None, values))
        value_min = min(filter(None, values))
        value_range = value_max - value_min
        if value_max == value_min:
            value_range = 1
        value = vector_manager.to_value(prop)

        if value:
            normalized = map(lambda v: (v - value) / value_range if v is not None else None, values)
        elif normalize_value_type == "max":
            normalized = map(lambda v: (value_max - v) / value_range if v is not None else None, values)
        elif normalize_value_type == "min":
            normalized = map(lambda v: (v - value_min) / value_range if v is not None else None, values)
        else:
            v_without_empty = filter(None, values)
            mean = reduce(lambda a, b: a + b, v_without_empty) / len(v_without_empty)
            normalized = map(lambda v: (v - mean) / value_range if v is not None else None, values)

        return normalized

    @classmethod
    def normalize(cls, values):
        return cls.__normalize(values)

    @classmethod
    def calc_more_is_better(cls, attr_name, item_list, selected_item=None):
        values = vector_manager.to_vector(attr_name, item_list)
        return cls.__normalize(values, normalize_value_type="min")

    @classmethod
    def calc_less_is_better(cls, attr_name, item_list, selected_item=None):
        values = vector_manager.to_vector(attr_name, item_list)
        return cls.__normalize(values, normalize_value_type="max")

    @classmethod
    def calc_near_is_better(cls, attr_name, item_list, selected_item):
        if selected_item and getattr(selected_item, attr_name):
            values = vector_manager.to_vector(attr_name, item_list)
            value = getattr(selected_item, attr_name)
            normalized = cls.__normalize(values, prop=value)
            normalized = map(lambda v: 1 - abs(v) if v is not None else None, normalized)
            return normalized
        else:
            raise NotCalculatable("selected item's " + attr_name + " is None")

    @classmethod
    def get_attributes(cls, instance):
        attributes = inspect.getmembers(instance, lambda a: not(inspect.isroutine(a)))
        attributes.extend(inspect.getmembers(instance, lambda a: inspect.isfunction(a)))
        # exclude private attribute
        return filter(lambda a: not(a[0].startswith("_")), attributes)

    def calc_score(self, item_list, selected_item=None):
        """
        calculate score and return ordered list
        :param item_list:
        :return:
        """

        attributes = self.__rules.keys()

        # initialize score vector by 0
        score_vector = map(lambda item: Scored(item), item_list)

        for attr_name in attributes:
            if attr_name in self.__rules:

                try:
                    attr_scores = self.__rules[attr_name](attr_name, item_list, selected_item)

                    # add score
                    for index, value in enumerate(score_vector):
                        total = 0
                        if attr_scores[index] is not None:
                            weight = 1 if not attr_name in self.__weights else self.__weights[attr_name]
                            total += weight * attr_scores[index]

                        score_vector[index].score += total
                        score_vector[index].set_score_detail(attr_name, total)

                except NotCalculatable as ex:
                    # when NotCalculatable, ignore calculation:
                    pass

        sorted_score = sorted(score_vector, key=lambda p: p.score, reverse=True)
        return sorted_score

    def make_pattern(self, item_list, selected_item):
        """
        make criticize pattern
        :param item_list:
        :param selected_item:
        :return:
        """

        # attributes = self.get_attributes()
        attributes = self.__rules.keys()

        pt_keys = []
        length = 0
        pt_judged = {}
        pt_counter = Counter()

        def judge_pattern(t_value, b_value):
            if t_value > b_value:
                return 1
            elif t_value < b_value:
                return -1
            else:
                return 0

        for a in attributes:
            name = a
            attribute_values = vector_manager.to_vector(name, item_list)
            selected_value = vector_manager.to_vector(name, [selected_item])[0]
            pt_keys.append(name)
            if length == 0:
                length = len(item_list)

            pt_judged.update({name: map(lambda a_v: judge_pattern(a_v, selected_value), attribute_values)})

        # make pattern
        for p_index in range(0, length):
            # single pattern & multiple(combination of two attribute) pattern
            for cnt in [1, 2]:
                for combi in itertools.combinations(pt_keys, cnt):
                    ptn = ",".join(combi)
                    p_ptn = "".join(map(lambda a_k: "X" if pt_judged[a_k][p_index] == 1 else "", combi))
                    n_ptn = "".join(map(lambda a_k: "X" if pt_judged[a_k][p_index] == -1 else "", combi))
                    if len(p_ptn) == cnt:
                        pt_counter["+:" + ptn] += 1
                    if len(n_ptn) == cnt:
                        pt_counter["-:" + ptn] += 1

        # order by support rate, and define pattern by at least two count
        patterns = filter(lambda p: p[1] > 1, pt_counter.items())
        patterns = map(lambda item: CriticizePattern(item[0], item[1] / length), patterns)
        patterns = sorted(patterns, key=lambda p: p.score)
        return patterns


class NotCalculatable(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class Scored(object):

    def __init__(self, item, score=0):
        self.item = item
        self.score = score
        self.score_detail = {}

    def set_score_detail(self, attribute_name, score):
        self.score_detail[attribute_name] = score
