import logging

from discord import Member
from discord.ext import commands

from .googledocs.ttt_sheet import FindTttTeam
from .googledocs.zrl import ZrlSignups, ZrlTeam, GetDiscordNames

logger = logging.getLogger(__name__)


class Sheet(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.discord_zid_map = None

    @commands.command(name='zrl', help='Shares the information to sign up for Backpedal ZRL teams')
    async def zrl(self, ctx):
        user = str(ctx.author).split('#')[0]
        current_signups = ZrlSignups()
        message='```Hey ' + user + '' \
                '\nZwift Racing League starts september 13th,\n' \
                + current_signups + ' sign-ups so far! Find the sign-up form at: ' \
                '```<https://forms.gle/XAmyvXpv5e72jpkMA>'
        await ctx.send(message)

    @commands.command(name='ttt-team', help='Shows the current ttt-team <name>')
    async def ttt_team(self, ctx, *args):
        if len(args) == 0:
            teams = []
            for i in range(1,6):
                tname = 'BAKPDL ' + str(i)
                teams.append(FindTttTeam(teamname=tname))
            message = '```Showing all Backpedal TTT team signups\n' + '\n'.join([team for team in teams]) + '```'
        else:
            message = '```' + FindTttTeam(teamname=' '.join(args)) + '```'
        await ctx.send(message)

    @commands.command(name='zrl-team', help='Shows the zrl-team <teamtag> "full"')
    async def zrl_team(self, ctx, *args):
        if len(args) != 1:
            if len(args) == 2 and args[1] == 'full':
                message = '```' + ZrlTeam(teamtag=args[0], full=True) + '```'
            else:
                message = '```Please type in !zrl-team <teamtag> "full". example: !zrl-team A1```'
        else:
            message = '```' + ZrlTeam(teamtag=args[0]) + '```'
        await ctx.send(message)

    async def discord_to_zwift_id(self, ctx, lookfor: Member) -> int:
        lookup_map = await self.discord_zwift_id_map(ctx)
        if lookfor.id in lookup_map:
            return lookup_map[lookfor.id][1]

    async def discord_zwift_id_map(self, ctx):
        names = GetDiscordNames()
        converter = commands.MemberConverter()
        if self.discord_zid_map is None:
            self.discord_zid_map = {}
            for name, zwid in names.items():
                try:
                    member = await converter.convert(ctx, name)
                    logger.debug("{0.id} -> {1}".format(member, zwid))
                    self.discord_zid_map[member.id] = (member, zwid)
                except commands.errors.MemberNotFound:
                    logger.debug("Not a member: {}".format(name))
        return self.discord_zid_map


def setup(bot):
    bot.add_cog(Sheet(bot))


def teardown(bot):
    pass
