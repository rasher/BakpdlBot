import traceback
import discord
from discord.ext import commands

intents = discord.Intents(message_content=True, messages=True)

bot = commands.Bot(command_prefix='!', intents=intents)
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
            await bot.load_extension(e)
        except Exception:
            traceback.print_exc()

