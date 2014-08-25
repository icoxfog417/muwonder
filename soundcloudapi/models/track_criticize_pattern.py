import enum
from knowbre import CriticizePattern, vector_utils
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

        # merge same questions
        merged = {}
        for s_p in questions:
            question = s_p["text"]
            if not question:
                continue

            if (not question in merged) or (question in merged and len(s_p["pattern"]) > len(merged[question]["pattern"])):
                merged[question] = s_p

        merged_questions = merged.values()
        return merged_questions

    def make_question(self, track, tracks):
        cr_targets = map(lambda ct: ct.name, self.get_targets())
        attr_for_pupular = [u"comment_count", u"download_count", u"playback_count", u"favoritings_count"]
        words = []
        pure_words = []

        def has_popular_attr():
            matches = map(lambda t: 1 if t in cr_targets else 0, attr_for_pupular)
            return sum(matches) > 0

        clusters, vectors = vector_utils.make_text_clusters(map(lambda t: t.tag_tokens(), tracks))
        target_vector = vector_utils.classify_text_tokens(track.tag_tokens(), clusters)

        if has_popular_attr():
            if self.is_positive():
                words.append(u"popular")
            else:
                words.append(u"minor")

        if u"elapsed" in cr_targets:
            words.append(u"recent")

        if u"bpm" in cr_targets:
            if self.is_positive():
                words.append(u"fast")
            else:
                words.append(u"slow")

        if u"genre_score" in cr_targets:
            #todo change term by genre_score
            words.append(u"active track" if self.is_positive() else u"calm track")

        if u"tag_tokens" in cr_targets:
            target_clusters = target_vector if self.is_positive() else map(lambda t: 1 if t == 0 else 0, target_vector)
            next_clusters = vector_utils.get_item_in_vector(clusters, target_clusters)
            if len(next_clusters) > 0:
                pure_words.append(next_clusters[0])

        text = u""
        if len(words) > 0:
            text += u"more" if self.is_positive() else u"less"
            text += u" " + u" and ".join(words)

        if len(pure_words) > 0:
            text += (u" and " if len(words) > 0 else u"") + u" and ".join(pure_words)

        if len(text) > 0:
            text = u"Do you like {0} track?".format(text)

        return {
            "pattern": self.pattern,
            "text": text
        }
