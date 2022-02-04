import logging
import os
import sys
from datetime import timedelta, date, datetime
from pathlib import Path
from typing import Dict

import ago
import click
import pendulum
from appdirs import user_cache_dir
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from requests_cache import CachedSession

from .zwiftpower.scraper import Scraper

load_dotenv()  # Not a fan of having this dangling here


def filter_catstr(cat):
    return {
        0: '',
        5: 'A+',
        10: 'A',
        20: 'B',
        30: 'C',
        40: 'D',
    }.get(cat, '?')


def flag_unicode(flag: str) -> str:
    r = ""
    if len(flag) == 2:
        for l in flag.upper():
            r += chr(0x1F1E6 - ord("A") + ord(l))
    elif len(flag) > 2:
        r += chr(0x1F3F4)
        for l in flag.lower().replace("-", ""):
            r += chr(0xE0061 - ord("a") + ord(l))
        r += chr(0xE007F)
    return r


def is_race(race: Dict) -> bool:
    return 'TYPE_RACE' in race['f_t']


def is_zrl(race: Dict) -> bool:
    return 'Zwift Racing League'.lower() in race['event_title'].lower()


def is_zrl_ttt(race: Dict) -> bool:
    if not is_zrl(race):
        return False

    ttt_dates = [
        # ZRL 20/21 Season 1
        date(2020, 10, 19), date(2020, 10, 20),  # Week 2
        date(2020, 11,  2), date(2020, 11,  3),  # Week 4
        date(2020, 11, 16), date(2020, 11, 17),  # Week 6
        date(2020, 11, 30), date(2020, 12,  1),  # Week 8
        date(2020, 12, 15), date(2020, 12, 16),  # Week 10
        # ZRL 20/21 Season 2
        date(2021,  1, 18), date(2021,  1, 19),  # Week 2
        date(2021,  2,  8), date(2021,  2,  9),  # Week 5
        date(2021,  3,  1), date(2021,  3,  2),  # Week 8
        # ZRL 20/21 Season 3
        date(2021,  4,  6), date(2021,  4,  7),  # Week 1
        date(2021,  4, 27), date(2021,  4, 28),  # Week 4
        date(2021,  5, 18), date(2021,  5, 19),  # Week 7
        date(2021,  6,  6), date(2021,  6,  7),  # Playoff TTT
        # ZRL 21/22 Season 1
        date(2021,  9, 28), date(2021,  9, 29),  # Week 1
        date(2021, 10,  8), date(2021, 10,  9),  # Week 7
        date(2021, 11, 23), date(2021, 11, 24),  # Playoff TTT
        # ZRL 21/22 Season 2
        date(2022,  2,  1), date(2022,  2,  2),  # Week 4
        date(2022,  2, 22), date(2022,  2, 23),  # Week 7
        date(2022,  3, 12), date(2022,  3, 13),  # Playoff TTT
    ]
    race_date = datetime.utcfromtimestamp(race['event_date'])
    return race_date.date() in ttt_dates


def is_wtrl_ttt(race: Dict) -> bool:
    return 'WTRL Team Time Trial' in race['event_title']


def is_frr_ttt(race: Dict) -> bool:
    title = race['event_title']
    return 'FRR' in title and 'TTT' in title


def is_ttt(race: Dict) -> bool:
    return is_wtrl_ttt(race) or is_zrl_ttt(race) or is_frr_ttt(race)


def filter_ttts(races):
    return filter(is_ttt, races)


def filter_races(races):
    return filter(is_race, races)


def filter_sdur(s):
    return ago.human(timedelta(seconds=s), past_tense="{}", precision=9, abbreviate=True)


class SourceType(click.ParamType):
    name = 'source'

    def convert(self, value, param, ctx):
        try:
            if ':' not in value:
                self.fail('Format must be type:id')
            type_, id_ = value.split(':', 1)
            types = ('team', 'race_results', 'race_signups', 'rider')
            if type_ not in types:
                self.fail('Unsupported type {}. Supported source types: {}'.format(type_, ", ".join(types)))
            return (type_, int(id_))
        except ValueError:
            self.fail('ID must be an integer')


class Getters:
    @staticmethod
    def team(scraper: Scraper, id_: int):
        """Return all riders on a team"""
        team = scraper.team(id_)
        return {
            'team': team,
            'riders': list(team.members),
        }

    @staticmethod
    def user(scraper: Scraper, id_: int):
        """Return a single user"""
        profile = scraper.profile(id_)
        return {'riders': [profile], 'rider': profile}

    @staticmethod
    def race_signups(scraper: Scraper, id_: int):
        """Return all signed-up riders on a race"""
        race = scraper.race(id_)
        return {
            'race': race,
            'riders': list(race.signups)
        }

    @staticmethod
    def race_results(scraper: Scraper, id_: int):
        """Return all riders in the results of a race"""
        race = scraper.race(id_)
        return {
            'race': race,
            'riders': list(race.results)
        }

    @staticmethod
    def race_unfiltered(scraper: Scraper, id_: int):
        """Return all riders in the results of a race"""
        race = scraper.race(id_)
        return {
            'race': race,
            'riders': list(race.unfiltered)
        }


@click.command()
@click.option('--clear-cache', is_flag=True)
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--output-file', type=click.Path(dir_okay=False, writable=True, allow_dash=True),
              help='Save output to file')
@click.option('--zwift-user', envvar='ZWIFT_USER', help='Will use environment ZWIFT_USER if set. Supports .env')
@click.option('--zwift-pass', envvar='ZWIFT_PASS', help='Will use environment ZWIFT_PASS if set. Supports .env')
@click.argument('rider_list', type=SourceType())
@click.argument('template')
def main(clear_cache, debug, zwift_user, zwift_pass, output_file, rider_list, template):
    """
    Output some sort of rider list with data downloaded from ZwiftPower

    \b
    Arguments:
    - RIDERLIST: Source of riders. Supported sources:
        - team:13264
        - rider:514482
        - race_results:2692522
        - race_unfiltered:2692522
        - race_signups:2692522
    - TEMPLATE: Jinja2 template to use to generate the output. Will be
                searched for either in CWD or from builtin templates.
    """
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level)
    source, id_ = rider_list

    expire_after = timedelta(hours=12)
    cache_dir = Path(user_cache_dir('riderlist'))
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = CachedSession(str(cache_dir / 'zp_cache'), expire_after=expire_after)
    if clear_cache:
        cached.cache.clear()
    s = Scraper(username=zwift_user, password=zwift_pass, sleep=2.0, session=cached)
    ctx = {
        'now': pendulum.now()
    }
    ctx.update(getattr(Getters, source)(s, id_))

    searchpaths = [
        Path(os.getcwd()),
        Path(__file__).parent / 'templates',
    ]
    env = Environment(loader=FileSystemLoader(searchpaths), undefined=StrictUndefined)

    env.filters['catstr'] = filter_catstr
    env.filters['ttts'] = filter_ttts
    env.filters['races'] = filter_races
    env.filters['flag2unicode'] = flag_unicode

    tpl = env.get_template(template)
    result = tpl.render(**ctx)

    with click.open_file(output_file, mode='w') as f:
        f.write(result)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
