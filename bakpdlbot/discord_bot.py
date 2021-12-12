# discord_bot.py
import os

#pip install -U python-dotenv==0.19.2
#pip install -U discord==1.7.3
from dotenv import load_dotenv

# 1
from discord.ext import commands

from googledocs.zrl import ZrlSignups
from googledocs.ttt_sheet import findteam

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 2
bot = commands.Bot(command_prefix='!')

@bot.command(name='sheet', help='Shares the link to the google sheet')
async def sheet(ctx):
    message='Find the google sheet at:\n' \
            '<https://docs.google.com/spreadsheets/d/16ip9cd6kpH2fl0dJYlG4UC1VOJL2eYjd8WSSXJMjss4/edit?usp=sharing>'
    await ctx.send(message)

@bot.command(name='events', help='Shares the link to backpedal zwift events')
async def events(ctx):
    message='Find our Backpedal events here:\n' \
            '<https://www.zwift.com/events/tag/backpedal>\n' \
            '<https://zwiftpower.com/series.php?id=BACKPEDAL>'
    await ctx.send(message)

@bot.command(name='zrl', help='Shares the information to sign up for Backpedal ZRL teams')
async def zrl(ctx):
    user = str(ctx.author).split('#')[0]
    current_signups = ZrlSignups()
    message='Hey ' + user + '' \
            '\nZwift Racing League starts january 11th,\n' \
            + current_signups + ' sign-ups so far! Find the sign-up form at: ' \
            '<https://forms.gle/ePGi4XVYoUkg4k6q9>'
    await ctx.send(message)

@bot.command(name='ttt-team', help='Shows the current ttt-team <name>')
async def events(ctx,*args):
    if len(args) == 0:
        teams = []
        for i in range(1,6):
            tname = 'BAKPDL ' + str(i)
            teams.append(findteam(teamname=tname))
        message = 'Showing all Backpedal TTT team signups\n' + '\n'.join([team for team in teams])
    else:
        message = findteam(teamname=' '.join(args))
    await ctx.send(message)


bot.run(TOKEN)
