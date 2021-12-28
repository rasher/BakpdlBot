import re
from datetime import timedelta

import ago
import discord
import pendulum

from discord.ext import commands

from .googledocs.zrl import ZrlSignups, ZrlTeam
from .googledocs.ttt_sheet import FindTttTeam
from . import zwift
from .zwift import Event


bot = commands.Bot(command_prefix='!')
TIMEZONE = pendulum.timezone("Europe/London")


async def event_embed(message, event):
    """Generate Embed object for a Zwift event"""
    cat_emoji = {}
    for c in 'ABCDE':
        cat_emoji[c] = discord.utils.get(message.guild.emojis, name='zcat' + c.lower())

    start = event.event_start
    embed = (
        discord.Embed(title=event.name, url=event.url)
            #.set_image(url=event.image_url)
            .add_field(name='Type', value=event.event_type.lower().replace('_', ' ').title())
            .add_field(name='Route', value=event.route)
            .add_field(name='World', value=event.map)
            .add_field(name='Start',
                       value="{:ddd MMM Do H:mm zz}".format(start.in_timezone(TIMEZONE)))
    )

    if event.distance_in_meters:
        embed.add_field(name='Distance', value='{:.1f} km'.format(event.distance_in_meters / 1000))
    elif event.duration_in_seconds:
        embed.add_field(name='Duration', value=ago.human(timedelta(seconds=event.duration_in_seconds), past_tense="{}"))
    elif event.laps:
        embed.add_field(name='Laps', value=event.laps)

    cats_text = []
    for subgroup in event.event_subgroups:
        cats_text.append("{s.event_subgroup_start:H:mm} {emoji} {s.from_pace_value:.1f}-{s.to_pace_value:.1f} w/kg".format(s=subgroup, emoji=cat_emoji[
            subgroup.subgroup_label]))
    embed.add_field(name='Cats', value="\n".join(cats_text), inline=False)

    footer = []
    for rule in event.rules_set:
        if rule == Event.NO_DRAFTING:
            footer.append('no draft')
        elif rule == Event.ALLOWS_LATE_JOIN:
            footer.append('late join')
    if 'doubledraft' in event.tags:
        footer.append('doubledraft')
    if footer:
        embed.set_footer(text=", ".join(footer))

    return embed


@bot.listen("on_message")
async def zwift_link_embed(message):
    if message.channel.name not in ('bot-test', 'looking-for-company', 'team-bus-event-talk'):
        return
    eventlink = re.compile(r'https://www.zwift.com/.*events/.*view/(?P<eid>[0-9]+)(?:\?eventSecret=(?P<secret>[0-9a-z]+))?')
    m = eventlink.search(message.content)
    if m:
        eid = int(m.group('eid'))
        secret = m.group('secret')
        event = zwift.get_event(eid, secret)
        embed = await event_embed(message, event)
        await message.reply(embed=embed)


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
    message='```Hey ' + user + '' \
            '\nZwift Racing League starts january 11th,\n' \
            + current_signups + ' sign-ups so far! Find the sign-up form at: ' \
            '```<https://forms.gle/ePGi4XVYoUkg4k6q9>'
    await ctx.send(message)

@bot.command(name='ttt-team', help='Shows the current ttt-team <name>')
async def events(ctx,*args):
    if len(args) == 0:
        teams = []
        for i in range(1,6):
            tname = 'BAKPDL ' + str(i)
            teams.append(FindTttTeam(teamname=tname))
        message = '```Showing all Backpedal TTT team signups\n' + '\n'.join([team for team in teams]) + '```'
    else:
        message = '```' + FindTttTeam(teamname=' '.join(args)) + '```'
    await ctx.send(message)

@bot.command(name='zrl-team', help='Shows the zrl-team <teamtag> "full"')
async def events(ctx,*args):
    if len(args) != 1:
        if len(args) == 2 and args[1] == 'full':
            message = '```' + ZrlTeam(teamtag=args[0], full=True) + '```'
        else:
            message = '```Please type in !zrl-team <teamtag> "full". example: !zrl-team A1```'
    else:
        message = '```' + ZrlTeam(teamtag=args[0]) + '```'
    await ctx.send(message)
