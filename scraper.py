import re
import time
import traceback
from pprint import pprint

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
            resp = self.scraper.session.get(url)
            if not getattr(resp, 'from_cache', False):
                time.sleep(self.scraper.sleep)
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
    URL = 'https://www.zwiftpower.com/profile.php?z=%d'

    def __init__(self, pid: int, scraper):
        super().__init__(scraper)
        self.pid = pid
        self._html = None

    @property
    def url(self):
        return self.URL % self.pid

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

    def __init__(self, sleep=None):
        self.session = HTMLSession()
        self.sleep = self.DEFAULT_SLEEP if sleep is None else sleep

    def get_profile(self, pid: int):
        p = Profile(pid, scraper=self)
        return p

    def get_team(self, tid: int):
        return Team(tid, scraper=self)

    def get_url(self, url: str) -> Response:
        resp = self.session.get(url)
        if not getattr(resp, 'from_cache', False):
            time.sleep(self.sleep)
        return resp

    def profile(self, pid):
        return Profile(pid, self)

    def team(self, tid):
        return Team(tid, self)


if __name__ == '__main__':
    s = Scraper(sleep=1.0)
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    for pid in [
        1412,
        4134,
        1557055,
        1567952,
        998676,
        2383255,
        2639298,
        1558036,
        1670475,
        802986,
        1646521,
    ]:
        p = s.profile(pid)
        print("{p.name} - {p.url}".format(p=p))
        pp = p.power_profile
        with open('%s_%d.html' % (ts, pid), 'w') as fp:
            fp.write(p.html.html)
        if None in (
                pp['wkg'][15]['value'],
                pp['wkg'][60]['value'],
                pp['wkg'][300]['value'],
                pp['wkg'][1200]['value']):
            pprint(pp)
            print(p.html.html)
            break
