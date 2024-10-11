import logging
import re
from datetime import timedelta

import ago
import discord
from discord import Member, PartialMessageable
from discord.ext import commands

from . import zwiftcom
from .sheet import Sheet
from .zwiftcom import Event
from .zwiftcom.const import items as list_of_items



logger = logging.getLogger(__name__)


class TimeTag:
    def __init__(self, datetime):
        self.datetime = datetime

    def _format(self, type_):
        return "<t:{0:.0f}:{1}>".format(self.datetime.timestamp(), type_)

    @property
    def short_time(self):
        return self._format('t')

    @property
    def long_time(self):
        return self._format('T')

    @property
    def short_date(self):
        return self._format('d')

    @property
    def long_date(self):
        return self._format('D')

    @property
    def long_date_short_time(self):
        return self._format('f')

    @property
    def long_date_short_time_dow(self):
        return self._format('F')

    @property
    def relative(self):
        return self._format('R')

    def __str__(self):
        return "<t:{0:.0f}>".format(self.datetime.timestamp())


async def event_embed(message, event, emojis=[]):
    """Generate Embed object for a Zwift event"""
    cat_emoji = {}
    for c in 'ABCDE':
        emoji = discord.utils.get(emojis, name='zcat' + c.lower())
        if emoji:
            cat_emoji[c] = emoji

    start = event.event_start
    embed = (
        discord.Embed(title=event.name.replace('|', r'\|'), url=event.url)
            # .set_image(url=event.image_url)
            .add_field(name='Type', value=event.event_type.lower().replace('_', ' ').title())
    )
    embed.description = 'https://zwiftpower.com/events.php?zid={0.id}'.format(event)

    # Check if subgroups are on separate worlds and/or routes
    same_world = len(set([sg.map for sg in event.event_subgroups])) == 1
    same_route = len(set([sg.route['signature'] for sg in event.event_subgroups])) == 1

    if same_route:
        embed.add_field(name='Route', value=event.route['name'])
    if same_world:
        embed.add_field(name='World', value=event.map)

    embed.add_field(name='Start', value=TimeTag(start).long_date_short_time_dow)

    if event.distance_in_meters:
        embed.add_field(name='Custom Distance', value='{:.1f} km'.format(event.distance_in_meters / 1000))
    elif event.duration_in_seconds:
        embed.add_field(name='Duration', value=ago.human(timedelta(seconds=event.duration_in_seconds), past_tense="{}"))
    elif event.laps:
        distance_m = event.route['leadinDistanceInMeters'] + (int(event.laps) * event.route['distanceInMeters'])
        embed.add_field(name='Laps', value="%d (%.1f km)" % (event.laps, distance_m/1000.0))

    cats_text = []
    footer = []
    for subgroup in event.event_subgroups:
        route = "" if same_route else ", {}".format(subgroup.route['name'])
        world = "" if same_world else " ({})".format(subgroup.map)

        cat_rules = ""
        for rule in subgroup.rules_set:
            if rule == Event.NO_DRAFTING:
                cat_rules = '(no draft)'
        for subtag in subgroup.tags:
            if 'trainer_difficulty_min' in subtag and not event.trainer_difficulty_min:
                cat_rules = cat_rules + f'(TD:{float(get_tag_value(subtag, False)):.0%})'
        if subgroup.range_access_label:
            access = "{s.range_access_label}".format(s=subgroup)
        else:
            access = "{s.from_pace_value:.1f}-{s.to_pace_value:.1f} w/kg".format(s=subgroup)
        cats_text.append(
            "{emoji} {start} {access}"
            "{route}{world} {cat_rules}".format(
                s=subgroup, emoji=cat_emoji.get(subgroup.subgroup_label, subgroup.subgroup_label,),
                route=route, world=world, cat_rules=cat_rules,
                start=TimeTag(subgroup.event_subgroup_start).short_time,
                access=access
            )
        )
    embed.add_field(name='Cats', value="\n".join(cats_text), inline=False)

    if event.powerups:
        pus = []
        for pu in event.powerups:
            pus.append(f'{pu} - {event.powerups[pu]}%')
        embed.add_field(name='Powerups', value="\n".join(pus), inline=False)

    if event.category_enforcement:
        footer.append('category enforcement')
    if event.trainer_difficulty_min:
        footer.append(f'TD:{float(event.trainer_difficulty_min):.0%}')
    for rule in event.rules_set:
        if rule == Event.NO_DRAFTING:
            footer.append('no draft')
        elif rule == Event.ALLOWS_LATE_JOIN:
            footer.append('late join')
        elif rule == Event.NO_ZPOWER:
            footer.append('no zpower riders')
        elif rule == Event.NO_POWERUPS:
            footer.append('no powerups')
        elif rule == Event.LADIES_ONLY:
            footer.append('ladies only')
        elif rule == Event.NO_TT_BIKES:
            footer.append('no tt bikes')

    if event.bike_hash is not None:
        embed.add_field(name='Fixed Bike', value=get_item(event.bike_hash))

    if event.jersey_hash is not None:
        embed.add_field(name='Fixed jersey', value=get_item(event.jersey_hash))

    for tag in event.tags:
        handle_tag = handle_event_tag(tag)
        if handle_tag is not None:
            footer.append(handle_tag)

    if footer:
        embed.set_footer(text=", ".join(footer))

    return embed

def handle_event_tag(tag):
    """Handle tag from events"""
    if tag == 'doubledraft':
        return 'doubledraft'
    elif tag == 'ttbikesdraft':
        return 'tt bikes draft'
    elif tag == 'jerseyunlock':
        return "jerseyunlock"
    elif 'bike_cda_bias' in tag:
        return f'CDA: {get_tag_value(tag, is_item=False)}'
    elif 'front_wheel_grams' in tag:
        return f'FW grams: {get_tag_value(tag, is_item=False)}'
    elif 'front_wheel_cda_bias' in tag:
        return f'FW CDA: {get_tag_value(tag, is_item=False)}'
    elif 'rear_wheel_grams' in tag:
        return f'RW grams: {get_tag_value(tag, is_item=False)}'
    elif 'rear_wheel_cda_bias' in tag:
        return f'RW CDA: {get_tag_value(tag, is_item=False)}'
    elif 'front_wheel_crr' in tag:
        return f'FW CRR: {get_tag_value(tag, is_item=False)}'
    elif 'fwheel_override' in tag:
        return f'FW override: {get_tag_value(tag)}'
    elif 'rwheeloverride' in tag:
        return f'RW override: {get_tag_value(tag)}'
    elif 'completionprize' in tag:
        return f'Completionprize: {get_tag_value(tag)}'
    return None

def get_tag_value(tag, is_item=True):
    """Obtain value from tag setting"""
    item_id = tag.split('=')[-1]
    if is_item is False:
        return item_id
    try:
        return get_item(int(item_id))
    except:
        return f"Unknown {item_id}"

def get_item(item_id):
    """Obtain item name from item id"""
    if item_id in list_of_items:
        return list_of_items[item_id]['name']
    return f"Unknown ({item_id})"

class Zwift(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.emojis = None

    @commands.Cog.listener("on_message")
    async def zwift_link_embed(self, message):
        if self.emojis is None:
            self.emojis = await message.guild.fetch_emojis()
        if isinstance(message.channel, PartialMessageable):
            channel = await self.bot.fetch_channel(message.channel.id)
            if channel.name in ('introductions', 'chit-chat', 'gallery', "ed's-little-blog"):
                return
        eventlink = re.compile(
            r'(?:https?:\/\/)(www.)?zwift.com/.*events/.*view/(?P<eid>[0-9]+)(?:\?eventSecret=(?P<secret>[0-9a-z]+))?')
        for m in eventlink.finditer(message.content):
            eid = int(m.group('eid'))
            secret = m.group('secret')
            event = zwiftcom.get_event(eid, secret)
            embed = await event_embed(message, event, emojis=self.emojis)
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


async def setup(bot):
    await bot.add_cog(Zwift(bot))


def teardown(bot):
    pass
