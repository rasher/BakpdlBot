import abc
import contextlib
import logging
import re
import time
import traceback

import demjson
import requests_html
from requests import Response, Session

logger = logging.getLogger(__name__)


def html(resp: Response):
    return requests_html.HTML(url=resp.url, html=resp.content)


class Fetchable(abc.ABC):

    def __init__(self, scraper):
        self.scraper = scraper

    def _get(self, selector):
        return self.html.find(selector, first=True)

    def _get_text(self, selector):
        elem = self._get(selector)
        if elem:
            return elem.text.strip()


class Rider:
    """
    A rider is a member of a team. A rider has some base data, but also a full Profile
    """
    def __init__(self, rider_data, scraper):
        self.data = rider_data
        self.profile = Profile(self.zwid, scraper=scraper)

    def __getattr__(self, item):
        return self.data.get(item, None)


class Race(Fetchable):
    URL = 'https://zwiftpower.com/events.php?zid={rid}'
    URL_SIGNUPS = 'https://zwiftpower.com/cache3/results/{rid}_signups.json'

    def __init__(self, rid, scraper):
        super().__init__(scraper)
        self.rid = rid
        self._signups = None
        self._html = None

    @property
    def html(self):
        if not self._html:
            resp = self.scraper.get_url(self.URL.format(rid=self.rid))
            self._html = html(resp)
        return self._html

    @property
    def signups(self):
        if not self._signups:
            url = self.URL_SIGNUPS.format(rid=self.rid)
            self._signups = self.scraper.get_url(url).json()
        for entrant in self._signups['data']:
            yield Rider(entrant, scraper=self.scraper)


class Team(Fetchable):
    URL = 'https://zwiftpower.com/team.php?id=%d'
    RIDERS = 'https://zwiftpower.com/api3.php?do=team_riders&id=%d&_=%d'

    def __init__(self, tid, scraper):
        super().__init__(scraper)
        self.tid = tid
        self._html = None
        self._riders_json = None

    @property
    def url(self):
        return self.URL % self.tid

    @property
    def html(self):
        if not self._html:
            resp = self.scraper.get_url(self.url)
            self._html = html(resp)
        return self._html

    @property
    def riders_json(self):
        if not self._riders_json:
            t = time.time()
            t -= t % 3600
            url = self.RIDERS % (self.tid, t)
            resp = self.scraper.get_url(url)
            self._riders_json = resp.json()
        return self._riders_json

    @property
    def riders(self):
        for r in self.riders_json['data']:
            yield Rider(r, scraper=self.scraper)

    @property
    def name(self):
        return self._get('input#team_name').attrs['value']

    @property
    def tag(self):
        return self._get('input#team_tag').attrs['value']

    @property
    def info(self):
        return self._get_text('textarea#team_info')

    @property
    def colors(self):
        return {
            'text': self._get('input#team_color').attrs['value'],
            'bg': self._get('input#team_bgcolor').attrs['value'],
            'border': self._get('input#team_bdcolor').attrs['value'],
        }


class Profile(Fetchable):
    URL_PROFILE = 'https://zwiftpower.com/profile.php?z={pid}'
    URL_RACES = 'https://zwiftpower.com/cache3/profile/{pid}_all.json'
    URL_CP = 'https://zwiftpower.com/api3.php?do=critical_power_profile&zwift_id={pid}&zwift_event_id=&type={type}'

    def __init__(self, pid: int, scraper):
        super().__init__(scraper)
        self.pid = pid
        self._html = None
        self._races = None
        self._cp_wkg = None
        self._cp_watts = None

    @property
    def url(self):
        return self.URL_PROFILE.format(pid=self.pid)

    @property
    def html(self):
        if not self._html:
            resp = self.scraper.get_url(self.url)
            self._html = html(resp)
        return self._html

    @property
    def cat(self):
        return self._get_text('table#profile_information span[title="Mixed 30 day category"]')

    @property
    def name(self):
        return self._get_text('div#zp_submenu a[href="#tab-results"]')

    @property
    def rank(self):
        s = self._get_text('#profile_information > tr:nth-child(1) > td > small > b:nth-child(2)')
        if s:
            return int(s.split("\n")[0].strip().replace(',', ''))

    @property
    def ftp(self):
        taglist = self.html.xpath("//th[normalize-space() = 'FTP'][1]/following-sibling::td[1]")
        if len(taglist) == 1:
            # 220w ~ 86kg
            return int(taglist[0].text.strip().split('w', 1)[0])
        else:
            logger.warning("Could not find ftp for %s", self.pid)
            return None

    @property
    def punch(self):
        s = self._get_text('#table_scroll_overview > div.btn-toolbar > div.pull-right > div.progress > div.progress-bar > span')
        m = re.search('Punch:\s*(?P<punch>[0-9\.]*)%', s)
        if m:
            return float(m.group('punch'))

    @property
    def races(self):
        if not self._races:
            url = self.URL_RACES.format(pid=self.pid)
            self._races = self.scraper.get_url(url).json()['data']
            self._races = list(filter(lambda e: e['event_date'] != '', self._races))
        return self._races

    @property
    def latest_race(self):
        r = sorted(self.races, key=lambda r: r['event_date'], reverse=True)
        if len(r) > 0:
            return r[0]
        return None

    @property
    def height(self):
        race = self.latest_race
        if not race:
            return None
        height = int(race['height'][0])
        return height if height > 0 else None

    @property
    def weight(self):
        race = self.latest_race
        if not race:
            return None
        weight = float(race['weight'][0])
        return weight if weight > 0 else None

    @property
    def cp_watts(self):
        if not self._cp_watts:
            url_watts = self.URL_CP.format(pid=self.pid, type='watts')
            self._cp_watts = self.scraper.get_url(url_watts).json()
        return {effort: {p['x']: p['y'] for p in data} for effort, data in self._cp_watts['efforts'].items()}

    @property
    def cp_wkg(self):
        if not self._cp_wkg:
            url_wkg = self.URL_CP.format(pid=self.pid, type='wkg')
            self._cp_wkg = self.scraper.get_url(url_wkg).json()
        return {effort: {p['x']: p['y'] for p in data} for effort, data in self._cp_wkg['efforts'].items()}

    @property
    def power_profile(self):
        """
        Power profile data from the User front-page, containing 15s, 60s, 5m and 20m power.
        It is not obvious whether this is 30 or 90 day data.

        See also :meth:`cp_watts` and :meth:`cp_wkg`
        :return: A dict of the form {'wkg':{15:1000,60:700,300:350,1200:270},'watt':{...}}
        :rtype: dict
        """
        try:
            sc = next(filter(lambda s: 'function load_profile_spider()' in s.text, self.html.find('script')))
            decoded = [self._decode_spider(x) for x in re.findall(r'{ mean:[^}]* }', sc.text)]
            ret = {
                'wkg': dict(zip([15, 60, 300, 1200], decoded[:4])),
                'watt': dict(zip([15, 60, 300, 1200], decoded[4:])),
            }
            return ret
        except (StopIteration, demjson.JSONDecodeError):
            traceback.print_exc()
            return {
               'wkg': {
                   15: {'pct': None, 'top': None, 'value': None},
                   60: {'pct': None, 'top': None, 'value': None},
                   300: {'pct': None, 'top': None, 'value': None},
                   1200: {'pct': None, 'top': None, 'value': None},
               },
               'watt': {
                   15: {'pct': None, 'top': None, 'value': None},
                   60: {'pct': None, 'top': None, 'value': None},
                   300: {'pct': None, 'top': None, 'value': None},
                   1200: {'pct': None, 'top': None, 'value': None},
               }
            }

    def __str__(self):
        return "{0.name} ({0.cat}) <{0.pid}>".format(self)

    def __repr__(self):
        return "<{} pid={}>".format(type(self).__name__, self.pid)

    @staticmethod
    def _decode_spider(x):
        values = demjson.decode(x)
        top = {
            '#f26f33': 1,
            '#0a7dce': 2,
            '#7CB5EC': 3,
        }
        return {
            'top': top.get(values['color'], None),
            'value': values['ours'].split(' ')[0],
            'pct': values['y'],
        }


class Scraper:
    DEFAULT_SLEEP = 5.0
    HOST = 'https://zwiftpower.com'
    ROOT = '/'

    def __init__(self, username: str, password: str, sleep: float = None, session: Session = None):
        self.sleep = self.DEFAULT_SLEEP if sleep is None else sleep
        self.session = session if session is not None else Session()
        self.session.headers.update({'User-Agent': requests_html.user_agent()})
        self._username = username
        self._password = password

    def get_url(self, url: str, is_login=False) -> Response:
        resp = self.session.get(url)
        resp.raise_for_status()
        if not is_login and not Scraper._is_logged_in(resp):
            logger.info("Logged out")
            if hasattr(resp, 'cache_key'):
                # If we're using requests-cache, evict the logged-out response
                self.session.cache.delete(resp.cache_key)
            self.login()
            resp = self.session.get(url)
            resp.raise_for_status()
        if not getattr(resp, 'from_cache', False):
            logger.debug("CACHE MISS: %s" % url)
            time.sleep(self.sleep)
        else:
            logger.debug("CACHE HIT:  %s" % url)
        return resp

    def profile(self, pid: int) -> Profile:
        return Profile(pid, scraper=self)

    def team(self, tid: int) -> Team:
        return Team(tid, scraper=self)

    def race(self, rid: int) -> Race:
        return Race(rid, scraper=self)

    def login(self):
        logger.debug("Logging in")
        if hasattr(self.session, 'cache_disabled'):
            logger.debug("Disabling cache")
            ctx = self.session.cache_disabled
        else:
            ctx = contextlib.nullcontext

        with ctx():
            logger.debug("Loading Zwiftpower Frontpage")
            frontpage_resp = self.get_url(self.HOST + self.ROOT, True)
            form = html(frontpage_resp).find('form#login', first=True)
            login_link = form.find('a')[0]
            zwift_login_url = login_link.attrs['href']

            logger.debug("Loading Zwift login <%s>", zwift_login_url)
            login_resp = self.get_url(zwift_login_url, True)
            form = html(login_resp).find('form#form', first=True)
            data = {}
            for inp in form.find('input'):
                data[inp.attrs['name']] = inp.attrs.get('value', None)
            del (data['rememberMe'])
            data['username'] = self._username
            data['password'] = self._password
            action = form.attrs['action'].strip()

            logger.debug("Submitting %r to %s", data, action)

            signon_resp = self.session.post(action, data)
            signon_resp.raise_for_status()
            if not self._is_logged_in(signon_resp):
                raise Exception("Could not log in")

    @staticmethod
    def _is_logged_in(resp: Response):
        return html(resp).find('form#login', first=True) is None
