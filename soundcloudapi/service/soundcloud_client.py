import soundcloud
from envs import Variable


def create():
    env = Variable()
    return soundcloud.Client(client_id=env.soundcloud_id)


def create_for_authorization(host_name):
    env = Variable()
    client = soundcloud.Client(
        client_id=env.soundcloud_id,
        client_secret=env.soundcloud_secret,
        redirect_uri="http://{0}/soundcloudapi/authorized".format(host_name)
    )
    return client


def create_by_token(token):
    env = Variable()
    return soundcloud.Client(access_token=token["access_token"])
