import enum
from knowbre import CriticizePattern
from soundcloudapi.models import Track


class TrackCriticizeType(enum.Enum):
    Pattern = 0
    Parameter = 1
    Like = 2


class TrackCriticizePattern(CriticizePattern):

    def __init__(self, pattern="", score=0.0):
        super(TrackCriticizePattern, self).__init__(pattern, score)

    @classmethod
    def patterns_to_questions(cls, patterns, track, tracks):
        questions = map(lambda c: c.make_question(track, tracks), patterns)

        def pattern_type(is_up):
            return "up_pattern" if is_up else "down_pattern"

        merged = {}
        for p in questions:
            for s_p in p:
                question = s_p["type"]

                if not question in merged:
                    merged[question] = {}
                    merged[question][pattern_type(s_p["is_up"])] = s_p["pattern"]
                    merged[question][pattern_type(not s_p["is_up"])] = ""
                elif not pattern_type(s_p["is_up"]) in merged[question]:
                    merged[question][pattern_type(s_p["is_up"])] = s_p["pattern"]
                elif len(s_p["pattern"]) > len(merged[question][pattern_type(s_p["is_up"])]):
                    merged[question][pattern_type(s_p["is_up"])] = s_p["pattern"]

        merged_array = []
        for key in merged:
            c = {"type": key}
            c.update(merged[key])
            merged_array.append(c)

        return merged_array

    def make_question(self, track, tracks):
        cr_targets = map(lambda ct: ct.name, self.get_targets())
        attr_for_pupular = ["comment_count", "download_count", "playback_count", "favoritings_count"]
        result = []

        def has_popular_attr():
            matches = map(lambda t: 1 if t in cr_targets else 0, attr_for_pupular)
            return sum(matches) > 0

        # clusters, vectors = vector_utils.make_text_clusters(map(lambda t: t.tag_tokens(), tracks))
        # target_vector = vector_utils.classify_text_tokens(track.tag_tokens(), clusters)

        if has_popular_attr():
            result.append({"pattern": self.pattern, "type": "Popularity", "is_up": self.is_positive()})

        if "elapsed" in cr_targets:
            result.append({"pattern": self.pattern, "type": "Created at", "is_up": self.is_positive()})

        """
        if "bpm" in cr_targets:
            if self.is_positive():
                words.append("fast")
            else:
                words.append("slow")
        """

        if "genre_score" in cr_targets:
            genre = Track.score_to_genre(track.genre_score())
            result.append({"pattern": self.pattern, "type": "Vibration", "is_up": self.is_positive()})
        elif "genre" in cr_targets:
            result.append({"pattern": self.pattern, "type": "Vibration", "is_up": self.is_positive()})

        """
        if "tag_tokens" in cr_targets:
            target_clusters = target_vector if self.is_positive() else map(lambda t: 1 if t == 0 else 0, target_vector)
            next_clusters = vector_utils.get_item_in_vector(clusters, target_clusters)
            if len(next_clusters) > 0:
                pure_words.append(next_clusters[0])
        """

        return result
