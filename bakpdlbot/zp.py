import io
import logging
import os
import typing
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

import ago
import discord
import matplotlib
import matplotlib.pyplot as plt
from appdirs import user_cache_dir
from discord.ext import commands
from discord.ext.commands import BadArgument
from requests_cache import CachedSession

from .zwiftpower.scraper import Scraper, Profile

logger = logging.getLogger(__name__)


def ago_fmt(v, _):
    td = timedelta(seconds=int(v))
    return ago.human(td, past_tense='{}', abbreviate=True).replace(', ', '')


def make_cp(plots, title, ylabel):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.set_title(title)
    ax.set_xscale('log')
    ax.set_ylabel(ylabel)
    ax.set_xticks([1, 2, 5, 10, 30, 60, 120, 300, 600, 1200, 3600, 7200, 14400, 36000])
    ax.set_xticks([], minor=True)
    formatter = matplotlib.ticker.FuncFormatter(ago_fmt)
    ax.xaxis.set_major_formatter(formatter)
    ax.grid(visible=True)
    for x, y, label in plots:
        line = ax.plot(x, y, label=label)
    ax.legend(loc='upper right')
    ax.set_xlim(left=1, right=None)
    return fig


def graph_type_conv(arg: str):
    a = arg.strip().lower()
    if a in ('wkg', 'w/kg'):
        return 'w/kg'
    elif a in ('watt', 'watts', 'raw'):
        return 'watt'
    else:
        raise BadArgument("Not a valid graph type: {}".format(arg))


class ZwiftPower(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        cache_dir = Path(user_cache_dir('bakpdlbot'))
        cache_dir.mkdir(parents=True, exist_ok=True)
        expire_after = timedelta(hours=12)
        cached = CachedSession(str(cache_dir / 'zp_cache'), expire_after=expire_after)
        load_dotenv()
        ZWIFTUSER = os.getenv('ZWIFT_USER')
        ZWIFTPASS = os.getenv('ZWIFT_PASS')
        ZWIFTTEAM = os.getenv('ZP_TEAM_ID')
        self.scraper = Scraper(sleep=1.0, username=ZWIFTUSER, password=ZWIFTPASS, session=cached)
        self.team = self.scraper.team(int(ZWIFTTEAM))

    @commands.command(name="cp", help="Show Critical Power")
    async def cp(self, ctx, graph_type: typing.Optional[graph_type_conv], *names):
        zwift = ctx.bot.get_cog('Zwift')
        ids = []
        errors = []
        for name in names:
            results = list((await zwift.zwift_id_lookup(ctx, name)).values())[0]
            if results is None or len(results) == 0:
                errors.append("No matches for {}".format(name))
            elif len(results) == 1:
                ids.append(results[0])
            else:
                errors.append("Too many matches ({}) for {}".format(len(results), name))

        async with ctx.typing():
            if len(ids) > 0:
                plots = []
                for profile in [self.scraper.profile(id_) for id_ in ids]:
                    # Make sure plots come out in order
                    cp = profile.cp_watts if graph_type == 'watt' else profile.cp_wkg
                    cp_data = sorted(cp['90days'].items(), key=lambda i: i[0])
                    plots.append(([i[0] for i in cp_data], [i[1] for i in cp_data], profile.name))
                fig = make_cp(plots, "90 day critical power", graph_type)
                fn = "cp_{}.png".format("_".join(map(str, ids)))
                file = self._fig_to_file(fig, fn)
                matplotlib.pyplot.close(fig)
            else:
                file = None
            await ctx.send("\n".join(errors), file=file)

    def find_team_member(self, q: str) -> typing.List[Profile]:
        logger.debug("Lookup <%s>", q)

        def exact(q: str):
            return lambda m: q.lower() == m.name.lower()

        def startswith(q: str):
            return lambda m: m.name.lower().startswith(q.lower())

        def contains(q: str):
            return lambda m: q.lower() in m.name.lower()

        members = list(self.team.members)
        for match_fn in [exact, startswith, contains]:
            matches = list(filter(match_fn(q), members))
            if len(matches) > 0:
                logging.debug("Found match(es) with %s for <%s>", match_fn.__name__, q)
                return [m.profile for m in matches]
        return []

    @staticmethod
    def _fig_to_file(fig, fn):
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        return discord.File(buf, filename=fn)


async def setup(bot):
    await bot.add_cog(ZwiftPower(bot))


def teardown(bot):
    pass
