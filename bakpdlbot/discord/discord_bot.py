# discord_bot.py
import os

from dotenv import load_dotenv

# 1
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 2
bot = commands.Bot(command_prefix='!')

@bot.command(name='sheet', help='shares the link to the google sheet')
async def testing(ctx):
    await ctx.send('Find the google sheet at:\nhttps://docs.google.com/spreadsheets/d/16ip9cd6kpH2fl0dJYlG4UC1VOJL2eYjd8WSSXJMjss4/edit?usp=sharing')

bot.run(TOKEN)
