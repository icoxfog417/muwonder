class SoundCloudResource(object):
    """
    Wrapper Class for soundcloud's Resource class to avoid AttributeError
    """

    def __init__(self, obj):
        self.obj = obj.fields()

    def __getstate__(self):
        return self.obj.items()

    def __setstate__(self, items):
        if not hasattr(self, 'obj'):
            self.obj = {}
        for key, val in items:
            self.obj[key] = val

    def __getattr__(self, name):
        if name in self.obj:
            return self.obj.get(name)
        else:
            # avoid exception
            return None

    def fields(self):
        return self.obj

    def keys(self):
        return self.obj.keys()