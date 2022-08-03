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

    # @commands.command(name='best', help='Shares info to Backpedal ESports Tour')
    # async def events(self, ctx):
    #     message = 'Backpedal ESports Tour:\n' \
    #               'Info: <https://docs.google.com/document/d/1LdUMQajmIAd7dB9tTG2VQ6isjfdcepscwnwRX9svezQ/edit?usp=sharing>\n' \
    #               'Standings: <https://docs.google.com/spreadsheets/d/1HF2M5XnX2tPilJrBrLa_jXZgJ8qX3OdJMhQ-QNPbxjY/edit?usp=sharing>\n' \
    #               'Sign-up: <https://forms.gle/EXUBf6hfbZmjerUZA>'
    #     await ctx.send(message)


def setup(bot):
    bot.add_cog(SimpleCommands(bot))


def teardown(bot):
    pass
