from discord.ext import commands
import traceback


class Admin(commands.Cog):

    def __init__(self, bot, extensions):
        self.bot = bot
        self.extensions = extensions

    @commands.command(name='reload', help='Reload extensions')
    @commands.is_owner()
    async def reload(self, ctx, *args):
        for e in self.extensions:
            try:
                await ctx.bot.reload_extension(e)
            except Exception:
                traceback.print_exc()

    @commands.command(name='load', help='Reload all extensions')
    @commands.is_owner()
    async def load(self, ctx, *args):
        for e in self.extensions:
            try:
                await ctx.bot.load_extension(e)
            except Exception:
                traceback.print_exc()


async def setup(bot):
    await bot.add_cog(Admin(bot, bot.EXTENSIONS))


def teardown(bot):
    pass
