import soundcloud_client
from knowbre.item_evaluator import ItemEvaluator, EvaluationType
from json_serialiable import JsonSerializable
from soundcloud_resource import SoundCloudResource


class User(JsonSerializable):

    def __init__(self, item=None):
        """
        create __client by secret client key to access soundcloud
        """
        super(User, self).__init__()
        self.id = u""
        self.username = u""
        self.permalink_url = u""
        self.country = u""
        self.full_name = u""
        self.track_count = 0
        self.playlist_count = 0
        self.followers_count = 0
        self.followings_count = 0
        self.public_favorites_count = 0

        self.__client = soundcloud_client.create()

        if item:
            self.set_param(item)

    def set_param(self, item):
        self.id = item.id
        self.username = item.username
        self.permalink_url = item.permalink_url
        self.country = item.country
        self.full_name = item.full_name
        self.track_count = item.track_count
        self.playlist_count = item.playlist_count
        self.followers_count = item.followers_count
        self.followings_count = item.followings_count
        self.public_favorites_count = item.public_favorites_count

    @classmethod
    def make_evaluator(cls):
        evaluator = ItemEvaluator()
        evaluator.set_rule("track_count", EvaluationType.MoreIsBetter)
        evaluator.set_rule("playlist_count", EvaluationType.MoreIsBetter)
        evaluator.set_rule("followers_count", EvaluationType.MoreIsBetter)
        evaluator.set_rule("public_favorites_count", EvaluationType.MoreIsBetter)

        evaluator.set_weight("followers_count", 2)  # the man who has many followers is better

        return evaluator

    def get_favorites(self):
        tracks = self.__client.get("/users/{0}/favorites".format(self.id))
        from .track import Track
        track_items = map(lambda t: Track(SoundCloudResource(t)), tracks)
        return track_items
