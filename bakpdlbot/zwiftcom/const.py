from datetime import timedelta
from pathlib import Path

from appdirs import user_cache_dir
from requests import Session
from requests_cache import CachedSession

# These aren't defined in the Game dictionary
worlds = {
    1: 'Watopia',
    2: 'Richmond',
    3: 'London',
    4: 'New York',
    5: 'Innsbruck',
    6: 'Bologna',
    7: 'Yorkshire',
    8: 'Crit City',
    9: 'Makuri Islands',
    10: 'France',
    11: 'Paris',
    12: 'Gravel Mountain',
    13: 'Scotland',
}


def retrieve_data(use_cache=True):
    url = 'https://www.zwift.com/zwift-web-pages/gamedictionary'
    if use_cache:
        cache_dir = Path(user_cache_dir('bakpdlbot'))
        cache_dir.mkdir(parents=True, exist_ok=True)
        expire_after = timedelta(hours=12)
        session = CachedSession(str(cache_dir / 'gd_cache'), expire_after=expire_after)
    else:
        session = Session()
    resp = session.get(url)
    return resp.json()['GameDictionary']


def sports(s):
    sports = {1: 'Cycling', 2: 'Running'}
    ret = []
    for value, sport in sports.items():
        if value & int(s):
            ret.append(sport)
    return ret


def comma_list(p):
    if p == "":
        return []
    return p.split(',') if ',' in p else [p]


def comma_list_int(p):
    return [int(v) for v in comma_list(p)] if p else []


def map_name(s):
    return {
        'MAKURIISLANDS': 'Makuri Islands',
        'NEWYORK': 'New York',
        'BOLOGNATT': 'Bologna',
        'CRITCITY': 'Crit City',
    }.get(s.upper(), s.title())


def id_to_world(id_):
    return worlds.get(int(id_))


def flip_dict(param):
    return dict([item for sublist in [[(vs, k) for vs in v] for k, v in param.items()]
                 for item in sublist])


def convert_item(item, section):
    convert_functions = {
        '__DEFAULTS__': {
            int: ['signature'],
        },
        'ROUTE': {
            int: ['xp', 'signature', 'levelLocked', 'duration', 'bikeType'],
            bool: ['supportsTimeTrialMode', 'supportedLaps', 'blockedForMeetups', 'eventOnly', 'bikeRec', 'rowRec',
                   'runRec'],
            float: ['distanceInMeters', 'difficulty', 'meetupLeadinAscentInMeters', 'meetupLeadinDistanceInMeters',
                    'leadinAscentInMeters', 'leadinDistanceInMeters', 'freeRideLeadinAscentInMeters',
                    'freeRideLeadinDistanceInMeters', 'ascentBetweenFirstLastLrCPsInMeters', 'ascentInMeters',
                    'distanceBetweenFirstLastLrCPsInMeters', 'defaultLeadinAscentInMeters',
                    'defaultLeadinDistanceInMeters'],
            sports: ['sports'],
            comma_list_int: ['eventPaddocks'],
            map_name: ['map'],
        },
        'BIKEFRAME': {
            bool: ['isTT'],
            int: ['modelYear']
        },
        'SEGMENT': {
            # TODO: World
            int: ['archId'],
            float: ['roadTime'],
            id_to_world: ['world'],
            comma_list_int: ['onRoutes'],
        },
        'NOTABLE_MOMENT_TYPE': {
            int: ['priority'],
        },
        'PORTAL_SEGMENT': {
            int: ['ArchID', 'Hash', 'JerseyFemaleHash', 'JerseyHash'],
            float: ['AverageSlope', 'CourseAscentF', 'CourseAscentR', 'CourseLength', 'Effort', 'MinCompletionTime'],
        }
    }

    # Turn the dict into a {key: fn} dict
    converters = flip_dict(convert_functions.get(section, {}))
    # Add the default ones
    default_converters = flip_dict(convert_functions['__DEFAULTS__'])
    converters.update(default_converters)

    return {k: converters.get(k, str)(v) for k, v in item.items()}


def object_key(o):
    return int(o['$']['signature'])


gamedictionary = {}
for plural, sublist in retrieve_data().items():
    if plural == '$':
        continue
    singular = list(sublist[0].keys())[0]
    gamedictionary[plural.lower()] = {object_key(r): convert_item(r['$'], singular) for r in sublist[0][singular]}

# Add segments on routes for no particular reason
for segment in gamedictionary['segments'].values():
    for route in segment.get('onRoutes', []):
        if route not in gamedictionary['routes']:
            continue
        if 'segments' not in gamedictionary['routes'][route]:
            gamedictionary['routes'][route]['segments'] = []
        gamedictionary['routes'][route]['segments'].append(segment['signature'])

routes = gamedictionary['routes']
segments = gamedictionary['segments']
jerseys = gamedictionary['jerseys']
runshirts = gamedictionary['runshirts']
runshorts = gamedictionary['runshorts']
runshoes = gamedictionary['runshoes']
bikeshoes = gamedictionary['bikeshoes']
bikefrontwheels = gamedictionary['bikefrontwheels']
bikerearwheels = gamedictionary['bikerearwheels']
bikeframes = gamedictionary['bikeframes']
paintjobs = gamedictionary['paintjobs']
socks = gamedictionary['socks']
glasses = gamedictionary['glasses']
headgears = gamedictionary['headgears']
achievements = gamedictionary['achievements']
challenges = gamedictionary['challenges']
notable_moment_types = gamedictionary['notable_moment_types']
unlockable_categories = gamedictionary['unlockable_categories']
training_plans = gamedictionary['training_plans']
portal_segments = gamedictionary['portal_segments']

items = {
    **bikeframes,
    **jerseys,
    **headgears,
    **socks,
    **paintjobs,
    **glasses,
    **bikeshoes,
    **bikefrontwheels,
    **bikerearwheels,
    **runshirts,
    **runshorts,
    **runshoes
}
