import re
import sys
import time
import traceback

import demjson
from requests import Response
from requests_html import HTMLSession


class Fetchable:

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
    URL = 'https://zwiftpower.com/events.php?zid=2350665'
    URL_SIGNUPS = 'https://zwiftpower.com/cache3/results/{rid}_signups.json'

    def __init__(self, rid, scraper):
        super().__init__(scraper)
        self.rid = rid
        self._signups = None

    @property
    def signups(self):
        if not self._signups:
            url = self.URL_SIGNUPS.format(rid=self.rid)
            self._signups = self.scraper.get_url(url).json()
        for entrant in self._signups['data']:
            yield Rider(entrant, scraper=self.scraper)


class Team(Fetchable):
    URL = 'https://www.zwiftpower.com/team.php?id=%d'
    RIDERS = 'https://www.zwiftpower.com/api3.php?do=team_riders&id=%d&_=%d'

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
            self._html = resp.html
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
    URL_PROFILE = 'https://www.zwiftpower.com/profile.php?z={pid}'
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
            self._html = resp.html
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
        tag = self.html.xpath("//th[normalize-space() = 'FTP'][1]/following-sibling::td[1]")[0]
        # 220w ~ 86kg
        return int(tag.text.strip().split('w', 1)[0])

    @property
    def punch(self):
        s = self._get_text('#table_scroll_overview > div.btn-toolbar > div.pull-right > div.progress > div.progress-bar > span')
        m = re.search('Punch: (?P<punch>[0-9\.]*)%', s)
        if m:
            return float(m.group('punch'))

    @property
    def races(self):
        if not self._races:
            url = self.URL_RACES.format(pid=self.pid)
            self._races = self.scraper.get_url(url).json()['data']
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
        return "{0.name} ({0.cat}) - {0.rank} {0.power_profile}".format(self)

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

    def __init__(self, username, password, sleep=None):
        self.sleep = self.DEFAULT_SLEEP if sleep is None else sleep
        self.session = HTMLSession()
        if hasattr(self.session, 'cache_disabled'):
            with self.session.cache_disabled():
                self._login(username, password)
        else:
            self._login(username, password)

    def get_url(self, url: str) -> Response:
        resp = self.session.get(url)
        if not getattr(resp, 'from_cache', False):
            sys.stderr.write("CACHE MISS: %s\n" % url)
            time.sleep(self.sleep)
        else:
            sys.stderr.write("CACHE HIT:  %s\n" % url)
        return resp

    def profile(self, pid: int) -> Profile:
        return Profile(pid, scraper=self)

    def team(self, tid: int) -> Team:
        return Team(tid, scraper=self)

    def race(self, rid: int) -> Race:
        return Race(rid, scraper=self)

    def _login(self, username, password):
        login_form_resp = self.get_url(self.HOST + self.ROOT)
        form = login_form_resp.html.find('form#login', first=True)
        data = {}
        for inp in form.find('input'):
            data[inp.attrs['name']] = inp.attrs.get('value', None)
        del(data['autologin'])
        del(data['viewonline'])
        data['username'] = username
        data['password'] = password
        action = form.attrs['action']

        signon_resp = self.session.post(self.HOST + '/' + action, data)
        if signon_resp.html.find('form#login', first=True) is not None:
            raise Exception("Not logged in")


if __name__ == '__main__':
    import os
    s = Scraper(sleep=1.0, username=os.environ.get('ZP_USER', ''), password=os.environ.get('ZP_PASS', ''))
    me = s.profile(514482)
    print("{p.name}: {p.height} cm, {p.weight} kg".format(p=me))
