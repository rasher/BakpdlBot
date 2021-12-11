# discord_bot.py
import os

#pip install -U python-dotenv==0.19.2
#pip install -U discord==1.7.3
from dotenv import load_dotenv

# 1
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 2
bot = commands.Bot(command_prefix='!')

@bot.command(name='sheet', help='shares the link to the google sheet')
async def sheet(ctx):
    message='Find the google sheet at:\n' \
            '<https://docs.google.com/spreadsheets/d/16ip9cd6kpH2fl0dJYlG4UC1VOJL2eYjd8WSSXJMjss4/edit?usp=sharing>'
    await ctx.send(message)

@bot.command(name='events', help='shares the link to backpedal zwift events')
async def events(ctx):
    message='Find our Backpedal events here:\n' \
            '<https://www.zwift.com/events/tag/backpedal>\n' \
            '<https://zwiftpower.com/series.php?id=BACKPEDAL>'
    await ctx.send(message)


bot.run(TOKEN)
