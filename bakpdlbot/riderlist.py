import csv
import io
import logging
import os
import sys
from datetime import timedelta, date, datetime
from pathlib import Path
from typing import Dict, List

import ago
import click
import matplotlib.pyplot
import pendulum
from appdirs import user_cache_dir
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from matplotlib.figure import Figure
from requests_cache import CachedSession

from .zwiftpower.scraper import Scraper
from . import zwiftracing

from .zp import make_cp, ago_fmt

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


def fig_to_svg(fig: Figure, prolog: bool = False):
    # Stupid monkey-patch to prevent xml prolog in output
    if not prolog:
        import matplotlib.backends.backend_svg as s
        if s.svgProlog:
            s.old_svgProlog = s.svgProlog
            s.svgProlog = ""

    imgdata = io.StringIO()
    fig.savefig(imgdata, format='svg')
    imgdata.seek(0)  # rewind the data

    svg_dta = imgdata.read()  # this is svg data
    matplotlib.pyplot.close(fig)

    if not prolog:
        s.svgProlog = s.old_svgProlog
    return svg_dta


def filter_cp_svg(riders, type_='wkg', style='default') -> str:
    plots = []
    title = "90 day CP"
    ylabel = type_

    for rider in riders:
        graph = rider.cp_watts if type_ == 'watts' else rider.cp_wkg
        if graph is None:
            continue
        graph = graph['90days']
        plots.append([graph.keys(), graph.values(), rider.name])
    ctx = matplotlib.pyplot.xkcd if style == 'xkcd' else lambda: matplotlib.pyplot.style.context(style)

    with ctx():
        fig = make_cp(plots, title, ylabel)

    return fig_to_svg(fig, False)


def filter_power_bars(riders, type_, period, style='default', direction='horizontal', value_labels=True) -> str:
    import matplotlib.pyplot as plt

    ctx = matplotlib.pyplot.xkcd if style == 'xkcd' else lambda: matplotlib.pyplot.style.context(style)
    with ctx():
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.set_title("90 day {} power".format(ago_fmt(period, None)))
        x = []
        y = []
        for rider in riders:
            graph = rider.cp_watts if type_ == 'watts' else rider.cp_wkg
            if graph is None:
                continue
            graph = graph['90days']
            x.append(rider.name)
            y.append(graph[period])
        if direction == 'vertical':
            ax.bar(x, y)
            ax.set_ylabel(type_)
        elif direction == 'horizontal':
            ax.barh(x, y)
            d = ax.set_xlabel(type_)
            if value_labels:
                for rect in ax.patches:
                    x, y = rect.get_width(), rect.get_y() + rect.get_height() / 2
                    label = x
                    plt.annotate(
                        label,
                        (x, y),
                        xytext=(-10, 0),
                        textcoords='offset points',
                        va='center',
                        ha='right'
                    )
        fig.tight_layout()

    return fig_to_svg(fig, False)


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
        # ZRL 21/22 Season 3
        date(2022,  4, 12), date(2022,  4, 13),  # Week 2
        date(2022,  5,  3), date(2022,  5,  4),  # Week 5
        # ZRL 22/23 Round 1
        date(2022,  9, 27), date(2022,  9, 28),  # Week 3
        # ZRL 22/23 Round 2
        date(2022, 11, 15), date(2022, 11, 16),  # Week 2
        date(2022, 12,  6), date(2022, 12,  7),  # Week 5
        # ZRL 22/23 Round 3
        date(2023,  1, 17), date(2023,  1, 18),  # Week 2
        date(2023,  2,  7), date(2023,  2,  8),  # Week 5
        # ZRL 23/24 Round 1
        date(2023,  9, 26), date(2023,  9, 27),  # Week 3
        date(2023, 10, 17), date(2023, 10, 18),  # Week 3
        # ZRL 23/24 Round 2
        date(2023, 11, 28), date(2023, 11, 29),  # Week 3
        date(2023, 12, 19), date(2023, 12, 20),  # Week 3
        # ZRL 23/24 Round 3
        date(2024,  2,  6), date(2024,  2,  7),  # Week 3
        date(2024,  2, 27), date(2024,  2, 28),  # Week 3
        # ZRL 24/25 Round 1
        date(2024,  9, 10), date(2024,  9, 11),  # Week 1
        date(2024, 10,  1), date(2024, 10,  2),  # Week 4
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


def filter_csv_dict(row, *args, **kwargs):
    string_io = io.StringIO()
    write_header=False
    if 'write_header' in kwargs:
        write_header = kwargs['write_header']
        del(kwargs['write_header'])
    writer = csv.DictWriter(string_io, row.keys(), *args, **kwargs)
    if write_header:
        writer.writeheader()
    writer.writerow(row)
    string_io.seek(0)
    return string_io.read()


class NamedVarType(click.ParamType):
    name = 'NAME=VALUE'

    def convert(self, value, param, ctx):
        if '=' not in value:
            self.fail('Format must be NAME=VALUE')
        return value.split('=', 1)


class SourceType(click.ParamType):
    name = 'source'

    def convert(self, value, param, ctx):
        try:
            if ':' not in value:
                self.fail('Format must be type:id')
            type_, id_ = value.split(':', 1)
            types = ('team', 'race_results', 'race_signups', 'riders')
            if type_ not in types:
                self.fail('Unsupported type {}. Supported source types: {}'.format(type_, ", ".join(types)))
            if type_ in ('riders',):
                return type_, list(map(int, id_.split(',')))
            else:
                return type_, int(id_)
        except ValueError:
            self.fail('ID must be an integer (comma-separated ints, where supported)')


class Getters:
    @staticmethod
    def team(scraper: Scraper, id_: int):
        """Return all riders on a team"""
        team = scraper.team(id_)
        zr_team = {r.rider_id: r for r in zwiftracing.Team(id_).riders()}
        return {
            'team': team,
            'zwiftracing': zr_team,
            'type': 'team',
            'riders': list(team.members),
        }

    @staticmethod
    def riders(scraper: Scraper, ids: List[int]):
        """Return profile(s) directly"""
        profiles = [scraper.profile(id_) for id_ in ids]
        return {
            'riders': profiles,
            'type': 'riders',
            'styles': matplotlib.pyplot.style.available
        }

    @staticmethod
    def race_signups(scraper: Scraper, id_: int):
        """Return all signed-up riders on a race"""
        race = scraper.race(id_)
        return {
            'race': race,
            'type': 'race_signups',
            'riders': list(race.signups)
        }

    @staticmethod
    def race_results(scraper: Scraper, id_: int):
        """Return all riders in the results of a race"""
        race = scraper.race(id_)
        return {
            'race': race,
            'type': 'race_results',
            'riders': list(race.results)
        }

    @staticmethod
    def race_unfiltered(scraper: Scraper, id_: int):
        """Return all riders in the results of a race"""
        race = scraper.race(id_)
        return {
            'race': race,
            'type': 'race_unfiltered',
            'riders': list(race.unfiltered)
        }


@click.command()
@click.option('--clear-cache', is_flag=True)
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--output-file', type=click.Path(dir_okay=False, writable=True, allow_dash=True),
              help='Save output to file', default="-")
@click.option('--zwift-user', envvar='ZWIFT_USER', help='Will use environment ZWIFT_USER if set. Supports .env')
@click.option('--zwift-pass', envvar='ZWIFT_PASS', help='Will use environment ZWIFT_PASS if set. Supports .env')
@click.option('--var', 'tplvars', multiple=True, default=[], help='Variable to pass to the template, may be repeated', type=NamedVarType())
@click.argument('rider_list', type=SourceType())
@click.argument('template')
def main(clear_cache, debug, zwift_user, zwift_pass, tplvars, output_file, rider_list, template):
    """
    Output some sort of rider list with data downloaded from ZwiftPower

    \b
    Arguments:
    - RIDERLIST: Source of riders. Supported sources:
        - team:13264
        - riders:514482,399078
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
        'scraper': s,
        'now': pendulum.now()
    }

    searchpaths = [
        Path(os.getcwd()),
        Path(__file__).parent / 'templates',
    ]
    env = Environment(loader=FileSystemLoader(searchpaths), undefined=StrictUndefined)

    env.filters['catstr'] = filter_catstr
    env.filters['ttts'] = filter_ttts
    env.filters['races'] = filter_races
    env.filters['flag2unicode'] = flag_unicode
    env.filters['cp_svg'] = filter_cp_svg
    env.filters['sdur'] = filter_sdur
    env.filters['powerbars_svg'] = filter_power_bars
    env.filters['csv_dict'] = filter_csv_dict

    tpl = env.get_template(template)
    with cached.cache_disabled():
        ctx.update(getattr(Getters, source)(s, id_))
    result = tpl.render(args=dict(tplvars), **ctx)

    with click.open_file(output_file, mode='w') as f:
        f.write(result)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
