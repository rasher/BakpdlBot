import re

import ago
import discord
import pendulum
from discord.ext import commands

from . import zwiftcom
from .zwiftcom import Event

TIMEZONE = pendulum.timezone("Europe/London")


async def event_embed(message, event):
    """Generate Embed object for a Zwift event"""
    cat_emoji = {}
    for c in 'ABCDE':
        cat_emoji[c] = discord.utils.get(message.guild.emojis, name='zcat' + c.lower())

    start = event.event_start
    embed = (
        discord.Embed(title=event.name, url=event.url)
            # .set_image(url=event.image_url)
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
        cats_text.append(
            "{s.event_subgroup_start:H:mm} {emoji} {s.from_pace_value:.1f}-{s.to_pace_value:.1f} w/kg".format(
                s=subgroup, emoji=cat_emoji[
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


class Zwift(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def zwift_link_embed(self, message):
        if message.channel.name not in (
        'bot-test', 'looking-for-company', 'team-bus-event-talk', 'bakpdl-festive-500', 'weekend-bunchy',
        'backpedal-hc-series'):
            return
        eventlink = re.compile(
            r'https://www.zwift.com/.*events/.*view/(?P<eid>[0-9]+)(?:\?eventSecret=(?P<secret>[0-9a-z]+))?')
        m = eventlink.search(message.content)
        if m:
            eid = int(m.group('eid'))
            secret = m.group('secret')
            event = zwiftcom.get_event(eid, secret)
            embed = await event_embed(message, event)
            await message.reply(embed=embed)


def setup(bot):
    bot.add_cog(Zwift(bot))


def teardown(bot):
    pass
