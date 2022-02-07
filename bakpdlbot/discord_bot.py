import traceback

from discord.ext import commands

bot = commands.Bot(command_prefix='!')
bot.EXTENSIONS = (
    'bakpdlbot.simple',
    'bakpdlbot.sheet',
    'bakpdlbot.zwift',
    'bakpdlbot.zp',
    'bakpdlbot.admin'
)


@bot.listen("on_ready")
async def load_extensions(*args):
    for e in bot.EXTENSIONS:
        try:
            bot.load_extension(e)
        except Exception:
            traceback.print_exc()

