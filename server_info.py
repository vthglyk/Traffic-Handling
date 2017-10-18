import json


_NOTFOUND = object()


class ServerInfo(object):

    def __init__(self, id, ip, no_misses):
        self.id = str(id)
        self.ip = str(ip)
        self.no_misses = no_misses

    def increase_misses(self, no_misses):
        self.no_misses += no_misses

    def __eq__(self, other):
        for attr in ['id', 'ip', "no_misses"]:
            v1, v2 = [getattr(obj, attr, _NOTFOUND) for obj in [self, other]]
            if v1 is _NOTFOUND or v2 is _NOTFOUND:
                return False
            elif v1 != v2:
                return False
        return True

    def __str__(self):
        return str(self.__dict__)


class ServerInfoEncoder(json.JSONEncoder):
    def default(self, obj):
        if not isinstance(obj, ServerInfo):
            return super(ServerInfoEncoder, self).default(obj)

        return obj.__dict__