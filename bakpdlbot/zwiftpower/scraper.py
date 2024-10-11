import abc
import contextlib
import logging
import re
import time
import traceback
from typing import Iterator, List
from html import unescape

import demjson3 as demjson
import requests_html
from requests import Response, Session
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

# Flag<=>Country as used by ZwiftPower. Probably incomplete.
flags = {
    'ad': 'Andorra',
    'ae': 'United Arab Emirates',
    'af': 'Afghanistan',
    'ag': 'Antigua and Barbuda',
    'ai': 'Anguilla',
    'al': 'Albania',
    'am': 'Armenia',
    'ao': 'Angola',
    'ar': 'Argentina',
    'as': 'American Samoa',
    'at': 'Austria',
    'au': 'Australia',
    'aw': 'Aruba',
    'ax': 'Aland Islands',
    'az': 'Azerbaijan',
    'ba': 'Bosnia and Herzegovina',
    'bb': 'Barbados',
    'bd': 'Bangladesh',
    'be': 'Belgium',
    'bf': 'Burkina Faso',
    'bg': 'Bulgaria',
    'bh': 'Bahrain',
    'bj': 'Benin',
    'bm': 'Bermuda',
    'bn': 'Brunei Darussalam',
    'bo': 'Bolivia',
    'br': 'Brazil',
    'bs': 'Bahamas',
    'bt': 'Bhutan',
    'by': 'Belarus',
    'bz': 'Belize',
    'ca': 'Canada',
    'cg': 'Congo',
    'ch': 'Switzerland',
    'ci': "Cote D'Ivoire",
    'cl': 'Chile',
    'cm': 'Cameroon',
    'cn': 'China',
    'co': 'Colombia',
    'cr': 'Costa Rica',
    'cu': 'Cuba',
    'cw': 'Curacao',
    'cy': 'Cyprus',
    'cz': 'Czech Republic',
    'de': 'Germany',
    'dj': 'Djibouti',
    'dk': 'Denmark',
    'do': 'Dominican Republic',
    'dz': 'Algeria',
    'ec': 'Ecuador',
    'ee': 'Estonia',
    'eg': 'Egypt',
    'eh': 'Western Sahara',
    'es': 'Spain',
    'et': 'Ethiopia',
    'fi': 'Finland',
    'fj': 'Fiji',
    'fk': 'Falkland Islands',
    'fm': 'Micronesia',
    'fo': 'Faroe Islands',
    'fr': 'France',
    'ga': 'Gabon',
    'gb': 'United Kingdom',
    'gb-eng': 'England',
    'gb-nir': 'Northern Ireland',
    'gb-sct': 'Scotland',
    'gb-wls': 'Wales',
    'gd': 'Grenada',
    'ge': 'Georgia',
    'gf': 'French Guiana',
    'gg': 'Guernsey',
    'gh': 'Ghana',
    'gi': 'Gibraltar',
    'gl': 'Greenland',
    'gm': 'Gambia',
    'gp': 'Guadeloupe',
    'gr': 'Greece',
    'gt': 'Guatemala',
    'gu': 'Guam',
    'gy': 'Guyana',
    'hk': 'Hong Kong',
    'hn': 'Honduras',
    'hr': 'Croatia',
    'ht': 'Haiti',
    'hu': 'Hungary',
    'id': 'Indonesia',
    'ie': 'Ireland',
    'il': 'Israel',
    'im': 'Isle of Man',
    'in': 'India',
    'iq': 'Iraq',
    'is': 'Iceland',
    'it': 'Italy',
    'je': 'Jersey',
    'jm': 'Jamaica',
    'jo': 'Jordan',
    'jp': 'Japan',
    'ke': 'Kenya',
    'kg': 'Kyrgyzstan',
    'km': 'Comoros', 'nu': 'Niue', 'pw': 'Palau',
    'kn': 'Saint Kitts and Nevis',
    'kp': 'North Korea',
    'kr': 'Korea, Republic of',
    'kw': 'Kuwait',
    'ky': 'Cayman Islands',
    'kz': 'Kazakhstan',
    'la': "Lao People's Dem Repub",
    'lb': 'Lebanon',
    'lc': 'Saint Lucia',
    'li': 'Liechtenstein',
    'lk': 'Sri Lanka',
    'lt': 'Lithuania',
    'lu': 'Luxembourg',
    'lv': 'Latvia',
    'ma': 'Morocco',
    'mc': 'Monaco',
    'md': 'Moldova',
    'me': 'Montenegro',
    'mg': 'Madagascar',
    'mk': 'Macedonia',
    'mm': 'Myanmar',
    'mn': 'Mongolia',
    'mo': 'Macao',
    'mp': 'Northern Mariana Islands',
    'mq': 'Martinique',
    'ms': 'Montserrat',
    'mt': 'Malta',
    'mu': 'Mauritius',
    'mw': 'Malawi',
    'mx': 'Mexico',
    'my': 'Malaysia',
    'mz': 'Mozambique',
    'na': 'Namibia',
    'nc': 'New Caledonia',
    'nf': 'Norfolk Island',
    'ng': 'Nigeria',
    'ni': 'Nicaragua',
    'nl': 'Netherlands',
    'no': 'Norway',
    'np': 'Nepal',
    'nr': 'Nauru',
    'nz': 'New Zealand',
    'om': 'Oman',
    'pa': 'Panama',
    'pe': 'Peru',
    'pf': 'French Polynesia',
    'pg': 'Papua New Guinea',
    'ph': 'Philippines',
    'pk': 'Pakistan',
    'pl': 'Poland',
    'pm': 'Saint Pierre and Miquelon',
    'pn': 'Pitcairn',
    'pr': 'Puerto Rico',
    'ps': 'Palestine',
    'pt': 'Portugal',
    'py': 'Paraguay',
    'qa': 'Qatar',
    're': 'Reunion',
    'ro': 'Romania',
    'rs': 'Serbia',
    'ru': 'Russian Federation',
    'rw': 'Rwanda',
    'sa': 'Saudi Arabia',
    'sb': 'Solomon Islands',
    'sc': 'Seychelles',
    'se': 'Sweden',
    'sg': 'Singapore',
    'sh': 'Saint Helena',
    'si': 'Slovenia',
    'sj': 'Svalbard and Jan Mayen',
    'sk': 'Slovakia',
    'sl': 'Sierra Leone',
    'sm': 'San Marino',
    'sn': 'Senegal',
    'sr': 'Suriname',
    'sv': 'El Salvador',
    'sx': 'Sint Maarten',
    'sy': 'Syrian Arab Republic',
    'sz': 'Swaziland',
    'tc': 'Turks and Caicos Islands',
    'td': 'Chad',
    'th': 'Thailand',
    'tk': 'Tokelau',
    'tm': 'Turkmenistan',
    'tn': 'Tunisia',
    'tr': 'Turkey',
    'tt': 'Trinidad and Tobago',
    'tv': 'Tuvalu',
    'tw': 'Taiwan',
    'tz': 'Tanzania',
    'ua': 'Ukraine',
    'ug': 'Uganda',
    'us': 'United States',
    'uy': 'Uruguay',
    'uz': 'Uzbekistan',
    'va': 'Holy See (Vatican)',
    'vc': 'Saint Vincent Grenadines',
    've': 'Venezuela',
    'vi': 'Virgin Islands, U.s.',
    'vn': 'Viet Nam',
    'vu': 'Vanuatu',
    'wf': 'Wallis and Futuna',
    'ws': 'Samoa',
    'ye': 'Yemen',
    'za': 'South Africa',
    'zm': 'Zambia',
}
countries = {country:flag for flag, country in flags.items()}


def decodeentities(s):
    if isinstance(s, str) and '&' in s:
        return unescape(s)
    return s


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

    @property
    def url(self):
        return self.URL.format(id=self.id)


class Rider:
    def __init__(self, rider_data, scraper, container):
        self.data = rider_data
        self.scraper = scraper
        self.container = container
        self._profile = None

    @property
    def id(self):
        return self.zwid

    @property
    def profile(self):
        if self._profile is None:
            self._profile = self.scraper.profile(self.id)
        return self._profile

    def __getattr__(self, item):
        return decodeentities(self.data.get(item, None))

    def __repr__(self):
        return "<{0.__class__.__name__} id={0.id}, name='{0.name}'>".format(self)


class Member(Rider):
    """
    A member of a team. A member has some base data, but also a full Profile
    """
    pass


class Entrant(Rider):
    @property
    def team(self):
        if self.tid:
            return self.scraper.team(self.tid)


class Race(Fetchable):
    URL = 'https://zwiftpower.com/events.php?zid={id}'
    URL_SIGNUPS = 'https://zwiftpower.com/cache3/results/{id}_signups.json'
    URL_RESULTS = 'https://zwiftpower.com/cache3/results/{id}_view.json'
    URL_UNFILTERED = 'https://zwiftpower.com/cache3/results/{id}_zwift.json'

    def __init__(self, id_, scraper):
        super().__init__(scraper)
        self.id = id_
        self._signups = None
        self._results = None
        self._unfiltered = None
        self._html = None

    @property
    def html(self):
        if not self._html:
            resp = self.scraper.get_url(self.URL.format(id=self.id))
            self._html = html(resp)
        return self._html

    @property
    def name(self):
        return self._get("h3").text.strip()


    @property
    def signups(self) -> Iterator[Entrant]:
        if not self._signups:
            url = self.URL_SIGNUPS.format(id=self.id)
            self._signups = self.scraper.get_url(url).json()
        for entrant in self._signups['data']:
            yield Entrant(entrant, scraper=self.scraper, container=self)

    @property
    def results(self) -> Iterator[Entrant]:
        if not self._results:
            url = self.URL_RESULTS.format(id=self.id)
            self._results = self.scraper.get_url(url).json()
        for entrant in self._results['data']:
            yield Entrant(entrant, scraper=self.scraper, container=self)

    @property
    def unfiltered(self) -> Iterator[Entrant]:
        if not self._unfiltered:
            url = self.URL_UNFILTERED.format(id=self.id)
            self._unfiltered = self.scraper.get_url(url).json()
        for entrant in self._unfiltered['data']:
            yield Entrant(entrant, scraper=self.scraper, container=self)

    @property
    def categories(self) -> List[str]:
        btns = self.html.find('.tab-content #t_results .btn-toolbar .btn-group:nth-child(2) button,'
                              '.tab-content #t_signups .btn-toolbar .btn-group:nth-child(1) button')
        return [btn.text.strip() for btn in btns][1:]


class Team(Fetchable):
    URL = 'https://zwiftpower.com/team.php?id={id}'
    RIDERS = 'https://zwiftpower.com/api3.php?do=team_riders&id={id}'

    def __init__(self, id_, scraper):
        super().__init__(scraper)
        self.id = id_
        self._html = None
        self._riders_json = None

    @property
    def url(self):
        return self.URL.format(id=self.id)

    @property
    def html(self):
        if not self._html:
            resp = self.scraper.get_url(self.url)
            self._html = html(resp)
        return self._html

    @property
    def riders_json(self):
        if not self._riders_json:
            url = self.RIDERS.format(id=self.id)
            resp = self.scraper.get_url(url)
            self._riders_json = resp.json()
        return self._riders_json

    @property
    def members(self) -> Iterator[Member]:
        for r in self.riders_json['data']:
            yield Member(r, scraper=self.scraper, container=self)

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

    def __repr__(self):
        return "<Team id={0.id}, name={0.name}>".format(self)


class Profile(Fetchable):
    URL_PROFILE = 'https://zwiftpower.com/profile.php?z={id}'
    URL_RACES = 'https://zwiftpower.com/cache3/profile/{id}_all.json'
    URL_CP = 'https://zwiftpower.com/api3.php?do=critical_power_profile&zwift_id={id}&zwift_event_id=&type={type}'

    def __init__(self, id_: int, scraper):
        super().__init__(scraper)
        self.id = id_
        self._html = None
        self._races = None
        self._cp_wkg = None
        self._cp_watts = None

    @property
    def url(self):
        return self.URL_PROFILE.format(id=self.id)

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
        return self.zftp

    @property
    def zftp(self):
        taglist = self.html.xpath("//th[normalize-space() = 'zFTP'][1]/following-sibling::td[1]")
        if len(taglist) == 1:
            # 220w ~ 86kg
            return int(taglist[0].text.strip().split('w', 1)[0])
        else:
            logger.warning("Could not find zFTP for %s", self.id)
            return None

    @property
    def punch(self):
        s = self._get_text('#table_scroll_overview > div.btn-toolbar > div.pull-right > div.progress > div.progress-bar > span')
        m = re.search(r'Punch:\s*(?P<punch>[0-9\.]*)%', s)
        if m:
            return float(m.group('punch'))

    @property
    def races(self):
        if not self._races:
            url = self.URL_RACES.format(id=self.id)
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
        taglist = self.html.xpath("//th[normalize-space() = 'FTP'][1]/following-sibling::td[1]")
        if len(taglist) == 1:
            # 220w ~ 86kg
            return float(taglist[0].text.strip().split('~', 1)[1].replace('kg', ''))
        # Fall back to using weight from latest race
        race = self.latest_race
        if not race:
            return None
        weight = float(race['weight'][0])
        return weight if weight > 0 else None

    @property
    def cp_watts(self):
        if not self._cp_watts:
            try:
                url_watts = self.URL_CP.format(id=self.id, type='watts')
                self._cp_watts = self.scraper.get_url(url_watts).json()
            except:
                traceback.print_exc()
                return None
        if not self._cp_watts or len(self._cp_watts['efforts']) == 0:
            return None
        return {effort: {p['x']: p['y'] for p in data} for effort, data in self._cp_watts['efforts'].items()}

    @property
    def cp_wkg(self):
        if not self._cp_wkg:
            url_wkg = self.URL_CP.format(id=self.id, type='wkg')
            self._cp_wkg = self.scraper.get_url(url_wkg).json()
        if not self._cp_wkg or len(self._cp_wkg['efforts']) == 0:
            return None
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

    @property
    def country(self):
        taglist = self.html.xpath("//th[normalize-space() = 'Country'][1]/following-sibling::td[1]")
        if len(taglist) == 1:
            # 220w ~ 86kg
            return taglist[0].text.strip()
        else:
            logger.warning("Could not find country for %s", self.id)
            return None

    @property
    def flag(self):
        country = self.country
        if country is not None:
            return countries.get(country)

    @property
    def rs(self):
        taglist = self.html.xpath("//th[normalize-space() = 'Zwift Racing Score'][1]/following-sibling::td[1]/b")
        if len(taglist) == 1:
            return taglist[0].text.strip()

    @property
    def team(self) -> Team:
        taglist = self.html.xpath("//th[normalize-space() = 'Team'][1]/following-sibling::td[1]/a")

        if len(taglist) == 1:
            href = taglist[0].attrs['href']
            parsed_url = urlparse(href)
            parsed_qs = parse_qs(parsed_url.query)
            if 'id' in parsed_qs:
                return Team(parsed_qs['id'][0], self.scraper)

    def __str__(self):
        return "{0.name} ({0.cat}) <{0.id}>".format(self)

    def __repr__(self):
        return "<{} id={}>".format(type(self).__name__, self.id)

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
        if not all([username, password]):
            raise Exception("Username or password empty")
        self.sleep = self.DEFAULT_SLEEP if sleep is None else sleep
        self.session = session if session is not None else Session()
        self.session.headers.update({'User-Agent': requests_html.user_agent()})
        self._username = username
        self._password = password

    def get_url(self, url: str, is_login=False) -> Response:
        logger.debug("GET %s", url)
        resp = self.session.get(url)
        # If we get a 403 or a login-page, do the login-dance
        if not is_login and (resp.status_code == 403 or not Scraper._is_logged_in(resp)):
            logger.warning("Logged out - logging in")
            if hasattr(resp, 'cache_key'):
                # If we're using requests-cache, evict the logged-out response
                self.session.cache.delete(resp.cache_key)
            self.login()
            logger.info("Login successful")
            resp = self.session.get(url)
            resp.raise_for_status()
        else:
            resp.raise_for_status()

        if not getattr(resp, 'from_cache', False):
            logger.debug("CACHE MISS: %s" % url)
            time.sleep(self.sleep)
        else:
            logger.debug("CACHE HIT:  %s" % url)
        return resp

    def profile(self, id_: int) -> Profile:
        return Profile(id_, scraper=self)

    def team(self, id_: int) -> Team:
        return Team(id_, scraper=self)

    def race(self, id_: int) -> Race:
        return Race(id_, scraper=self)

    def login(self):
        logger.debug("Logging in")
        # If we're using a cached session, disable it for login
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
