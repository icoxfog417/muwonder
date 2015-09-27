import soundcloud
import secret_settings


def create_for_authorization(host_name):
    client = soundcloud.Client(
        client_id=secret_settings.SOUND_CLOUD_ID,
        client_secret=secret_settings.SOUND_CLOUD_SECRET,
        redirect_uri="http://{0}/soundcloudapi/authorized".format(host_name)
    )
    return client


def create_by_token(token):
    return soundcloud.Client(access_token=token[u"access_token"], proxies=get_proxy())


def create():
    return soundcloud.Client(client_id=secret_settings.SOUND_CLOUD_ID, proxies=get_proxy())


def get_proxy():
    proxy = {}
    if secret_settings.HTTP_PROXY:
        proxy["http"] = secret_settings.HTTP_PROXY
