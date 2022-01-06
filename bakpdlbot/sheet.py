from discord.ext import commands

from .googledocs.zrl import ZrlSignups, ZrlTeam, GetZwiftIdFromSheet
from .googledocs.ttt_sheet import FindTttTeam


class Sheet(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='zrl', help='Shares the information to sign up for Backpedal ZRL teams')
    async def zrl(self, ctx):
        user = str(ctx.author).split('#')[0]
        current_signups = ZrlSignups()
        message='```Hey ' + user + '' \
                '\nZwift Racing League starts january 11th,\n' \
                + current_signups + ' sign-ups so far! Find the sign-up form at: ' \
                '```<https://forms.gle/ePGi4XVYoUkg4k6q9>'
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

    @commands.command(name='zwiftid', help='Searches zwiftid of name')
    async def zwiftid(self, ctx, *args):
        if len(args) == 0:
            message = '```Please type in !zwiftid <name>```'
        else:
            searchname= ' '.join(args)
            zwiftid, nrfound = GetZwiftIdFromSheet(name=searchname)
            if nrfound == 1:
                message = '```Zwiftid for ' + searchname + ':\n' + zwiftid + \
                        "\nCheck " + searchname + "'s profile on Zwiftpower:```\n" \
                        "<https://zwiftpower.com/profile.php?z=" + zwiftid + ">"
            else:
                message = '```Zwiftid for ' + searchname + ':\n' + zwiftid + ' ' + '```'
        await ctx.send(message)


def setup(bot):
    bot.add_cog(Sheet(bot))


def teardown(bot):
    pass
