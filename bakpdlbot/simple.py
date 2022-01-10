from discord.ext import commands


class SimpleCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='sheet', help='Shares the link to the google sheet')
    async def sheet(self, ctx):
        message='Find the google sheet at:\n' \
                '<https://docs.google.com/spreadsheets/d/16ip9cd6kpH2fl0dJYlG4UC1VOJL2eYjd8WSSXJMjss4/edit?usp=sharing>'
        await ctx.send(message)

    @commands.command(name='events', help='Shares the link to backpedal zwift events')
    async def events(self, ctx):
        message='Find our Backpedal events here:\n' \
                '<https://www.zwift.com/events/tag/backpedal>\n' \
                '<https://zwiftpower.com/series.php?id=BACKPEDAL>'
        await ctx.send(message)


def setup(bot):
    bot.add_cog(SimpleCommands(bot))


def teardown(bot):
    pass
