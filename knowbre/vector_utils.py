import inspect
import math
from collections import Counter, defaultdict


def to_value(prop):
    if inspect.isfunction(prop):
        return prop()
    else:
        return prop


def to_vector(attr_name, item_list):
    def attribute_to_value(obj, name):
        if obj:
            v = getattr(obj, name)
            return to_value(v)
        else:
            return None

    attr_vector = map(lambda el: attribute_to_value(el, attr_name), item_list)
    return attr_vector


def __make_text_cluster_key(token):
    return token.lower().strip()


def classify_text_tokens(text_tokens, cluster):
    v = []
    arranged_tokens = map(__make_text_cluster_key, text_tokens)
    for c_i, c_t in enumerate(cluster):
        if c_t and c_t in arranged_tokens:
            v.append(1)
        else:
            v.append(0)

    return v


def make_text_clusters(list_of_text_tokens, cluster_count=-1):
    if not list_of_text_tokens or len(list_of_text_tokens) == 0:
        return [], []

    all_tokens = reduce(lambda x, y: x + y, list_of_text_tokens)
    clusters = Counter()
    for t in all_tokens:
        clusters[__make_text_cluster_key(t)] += 1

    chosen_clusters = []
    if cluster_count < 0:
        chosen_clusters = clusters.most_common()
    else:
        chosen_clusters = clusters.most_common(cluster_count)

    cluster_tokens = map(lambda c: c[0], chosen_clusters)
    classified_vector = map(lambda tokens: classify_text_tokens(tokens, cluster_tokens), list_of_text_tokens)

    return cluster_tokens, classified_vector


def calc_vector_distance(v1, v2):
    if len(v1) != len(v2):
        raise Exception("Length of Vector differ")

    squared_diff = []
    for i, value in enumerate(v1):
        squared_diff.append(math.pow(v1[i] - v2[i], 2))

    distance = math.sqrt(sum(squared_diff))
    return distance


def get_item_in_vector(v, targets):
    result = []
    for index, zero_one in enumerate(targets):
        if int(zero_one) == 1:
            result.append(v[index])

    return result
