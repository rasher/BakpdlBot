import logging
import re
from datetime import timedelta

import ago
import discord
import pendulum
from discord import Member
from discord.ext import commands

from . import zwiftcom
from .sheet import Sheet
from .zwiftcom import Event

TIMEZONE = pendulum.timezone("Europe/London")

logger = logging.getLogger(__name__)


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
    )
    embed.description = 'https://zwiftpower.com/events.php?zid={0.id}'.format(event)

    # Check if subgroups are on separate worlds and/or routes
    same_world = len(set([sg.map for sg in event.event_subgroups])) == 1
    same_route = len(set([sg.route for sg in event.event_subgroups])) == 1

    if same_route:
        embed.add_field(name='Route', value=event.route)
    if same_world:
        embed.add_field(name='World', value=event.map)

    embed.add_field(name='Start', value="{:ddd MMM Do H:mm zz}".format(start.in_timezone(TIMEZONE)))

    if event.distance_in_meters:
        embed.add_field(name='Distance', value='{:.1f} km'.format(event.distance_in_meters / 1000))
    elif event.duration_in_seconds:
        embed.add_field(name='Duration', value=ago.human(timedelta(seconds=event.duration_in_seconds), past_tense="{}"))
    elif event.laps:
        embed.add_field(name='Laps', value=event.laps)

    cats_text = []
    for subgroup in event.event_subgroups:
        route = "" if same_route else ", {}".format(subgroup.route)
        world = "" if same_world else " ({})".format(subgroup.map)
        cats_text.append(
            "{s.event_subgroup_start:H:mm} {emoji} {s.from_pace_value:.1f}-{s.to_pace_value:.1f} w/kg"
            "{route}{world}".format(
                s=subgroup, emoji=cat_emoji[subgroup.subgroup_label],
                route=route, world=world
            )
        )
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
        for m in eventlink.finditer(message.content):
            eid = int(m.group('eid'))
            secret = m.group('secret')
            event = zwiftcom.get_event(eid, secret)
            embed = await event_embed(message, event)
            await message.reply(embed=embed)

    @commands.command(name='zwiftid', help='Searches zwiftid of name')
    async def zwift_id(self, ctx, *args):
        zp = ctx.bot.get_cog('ZwiftPower')
        results = {}
        for query, ids in (await self.zwift_id_lookup(ctx, *args)).items():
            if ids is not None and 0 < len(ids) <= 5:
                results[query] = " / ".join(["{p.id} ({p.name})".format(p=zp.scraper.profile(id_)) for id_ in ids])
            else:
                results[query] = "Not found or too many results"
        await ctx.send("\n".join(["{0}: {1}".format(q, r) for q, r in results.items()]))

    async def zwift_id_lookup(self, ctx, *args):
        zp = ctx.bot.get_cog('ZwiftPower')
        sheet: Sheet = ctx.bot.get_cog('Sheet')
        converter = commands.MemberConverter()

        results = {}
        for query in args[:5]:
            logger.info("Looking up zwift id of <%s>", query)

            # First see if it's simply an int
            try:
                results[query] = [int(query)]
                continue
            except ValueError as e:
                pass

            try:
                member: Member = await converter.convert(ctx, query)
                query = member.display_name
                logger.info("Query is a Member - <using %s>", member.display_name)
            except commands.errors.MemberNotFound:
                pass

            # See if we can find a match for the string on the ZP team
            team_member_results = zp.find_team_member(query)
            if len(team_member_results) > 0:
                results[query] = [p.id for p in team_member_results]
                continue

            # See if the input is a Member and look for it int he ZRL sheet
            # It's slow and not very useful. Skip for now
            #try:
            #    member = await converter.convert(ctx, query)
            #    zid = await sheet.discord_to_zwift_id(ctx, member)
            #    if zid:
            #        results[query] = [zid]
            #        continue


            results[query] = None
        return results


def setup(bot):
    bot.add_cog(Zwift(bot))


def teardown(bot):
    pass
