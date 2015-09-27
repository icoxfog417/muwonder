class Variable():

    def __init__(self):
        import os

        local = {}
        local_path = os.path.join(os.path.dirname(__file__), "./local_envs.json")
        if os.path.isfile(local_path):
            import json
            with open(local_path, "r", encoding="utf-8") as f:
                local = json.load(f)

        get_env = lambda k, d="__DEFAULT_SETTING__": os.environ.get(k, d if k not in local else local[k])
        self.secret_token = get_env("SECRET_TOKEN")
        self.soundcloud_id = get_env("SOUND_CLOUD_ID")
        self.soundcloud_secret = get_env("SOUND_CLOUD_SECRET")
        self.http_proxy = get_env("HTTP_PROXY", "")
        self.database_user = get_env("DATABASE_USER", "muwonder")
        self.database_password = get_env("DATABASE_PASSWORD", "muwonder")
