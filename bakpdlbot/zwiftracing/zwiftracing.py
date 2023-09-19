import pprint
import requests

SITE = "https://www.zwiftracing.app"
API = SITE + "/api"


class JsonWrapper:
    def __init__(self, json):
        self._raw = json

    def __getattr__(self, item):
        key = self.__to_camel(item)
        item = self.raw.get(key)
        return self.__class__.wrap_object(item)

    def __to_camel(self, s):
        camel = ''.join(word.title() for word in s.split('_'))
        return camel[0].lower() + camel[1:]

    @property
    def raw(self):
        return self._raw

    def __str__(self):
        return str(pprint.pformat(self.raw))

    def __repr__(self):
        return repr(self.raw)

    @classmethod
    def wrap_object(cls, o):
        if isinstance(o, dict):
            return JsonWrapper(o)
        elif isinstance(o, list):
            return [cls.wrap_object(i) for i in o]
        else:
            return o


class Team:
    def __init__(self, id_: int):
        self.id = id_

    def riders(self, limit=None):
        url = API + '/riders'
        params = {
            'club': self.id,
            'page': 0,
            'pageSize': 50 if limit is None else min(limit, 50),
            'sortBy': 'points',
            'sortDirection': 'desc'
        }
        i = 0
        while True:
            result = requests.get(url, params).json()

            if 'riders' in result:
                if len(result['riders']) == 0:
                    break
                for rider in result['riders']:
                    i += 1
                    if limit is not None and limit < i:
                        break
                    yield JsonWrapper(rider)
            next_rider_number = 1 + (1+params['page']) * params['pageSize']
            if 'totalResults' in result and (next_rider_number > result['totalResults']) or (
                limit is not None and limit < next_rider_number):
                break
            params['page'] += 1
