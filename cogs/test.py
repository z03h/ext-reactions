import random
from datetime import datetime

import discord
from discord.ext import commands
import humanize

from Z.ReactionCommand import reaction_command
class Test(commands.Cog, command_attrs=dict(case_insensitive=True)):
    def __init__(self, bot):
        self.bot = bot

    def humanize_td(self, td):
        if not td.days:
            minimum = 'minutes'
        elif td.days <= 30:
            minimum = 'hours'
        elif 335 <= td.days % 365 <= 365  or (td.days < 365) or  0 <= td.days % 365 <= 30:
            minimum = 'days'
        else:
            minimum = 'months'
        return humanize.precisedelta(td, minimum_unit=minimum, format="%.0f").replace(' and', '').replace(',', '')

    @reaction_command(['\U0001f1fa\U0001f1ee'])
    @commands.guild_only()
    async def userinfo(self, ctx):
        """gets user id, create/join date, roles"""
        user = ctx.author
        now = datetime.utcnow()

        av_url = str(user.avatar_url_as(static_format='png'))
        name = '{}{}'.format(str(user), f'  •  {user.nick}' if user.nick else '')
        title = discord.utils.escape_markdown(name)
        embed = discord.Embed(title=title, olour=user.colour.value & 0xFFFFFE, timestamp=datetime.utcnow(),
                              url=av_url)
        embed.set_thumbnail(url=av_url)

        badges = {discord.UserFlags.staff: (733977728553844747,),
                  discord.UserFlags.partner: (750849757911449640,),
                  discord.UserFlags.hypesquad: (733977728428277851,),
                  discord.UserFlags.bug_hunter: (733977728415694858,),
                  discord.UserFlags.hypesquad_bravery: (733977728306643005,),
                  discord.UserFlags.hypesquad_brilliance: (733977728381878363,),
                  discord.UserFlags.hypesquad_balance: (733977728424083486,),
                  discord.UserFlags.early_supporter: (733977728201785396,),
                  discord.UserFlags.team_user: (),
                  discord.UserFlags.system: (733989940852949012, 733989940613873715,),
                  discord.UserFlags.bug_hunter_level_2: (750847507067568209,),
                  discord.UserFlags.verified_bot: (),
                  discord.UserFlags.verified_bot_developer: (733977728356843560,),
                 }
        badge_text = []
        for b in user.public_flags.all():
            for b_eid in badges.get(b, ()):
                badge_text.append(str(self.bot.get_emoji(b_eid)))
        if user.premium_since:
            premium_since = user.premium_since.strftime('%b %d, %Y')
            since = self.humanize_td(now-user.premium_since)
            booster = '\n__Boosting since__ {}\n`{}`<a:pepeboost:726009263063040030>'.format(premium_since, since)
        else:
            booster = ''
        bot_text = user.bot and ' <:bot1:721808209395843143><:bot2:721808220234055680>' or ''
        desc = '> {}{} \u00a0\u00a0{}{}'.format(user.mention, bot_text, ''.join(badge_text), booster)
        embed.description = desc

        # datetimes for joined guild / created account
        dtcreated = user.created_at.strftime('%d %b, %Y %H:%M')
        if now.day == user.created_at.day and now.month == user.created_at.month and now.year != user.created_at.year:
            dtcreated += ' \U0001f382'
        td_created = self.humanize_td(now - user.created_at)
        embed.add_field(name='__Joined Discord__', value='{}\n`{}`'.format(dtcreated, td_created))
        dtjoined = user.joined_at.strftime('%d %b, %Y %H:%M')
        if now.day == user.joined_at.day and now.month == user.joined_at.month and now.year != user.joined_at.year:
            dtjoined += ' \U0001f382'
        td_joined = self.humanize_td(now - user.joined_at)
        embed.add_field(name='__Joined Server__', value='{}\n`{}`'.format(dtjoined, td_joined))
        # calculate roles
        text_len = 0
        allroles = []
        first = True
        # make sure roles don't exceed embed field char limit
        for role in reversed(user.roles[1:]):
            text_len += len(role.mention)
            allroles.append(role.mention)
            if text_len > 900:
                embed.add_field(name=first and '__Roles__({:,})'.format(len(user.roles) - 1) or '\u200b', value=' | '.join(allroles) or '\u200b', inline=False)
                allroles = []
                text_len = 0
                first = False
        else:
            embed.add_field(name=first and '__Roles__({:,})'.format(len(user.roles) - 1) or '\u200b', value=' | '.join(allroles) or '\u200b', inline=False)
        #for sorting members by join date
        sortmembers = sorted(ctx.guild.members, key=lambda m: m.joined_at)
        footertext = 'Member# {:,}  •  User ID: {}'.format(sortmembers.index(user)+1, user.id)
        embed.set_footer(text=footertext, icon_url=user.avatar_url_as(static_format='png', size=32))
        await ctx.send(embed=embed)

    @reaction_command('\U0001f1f8\U0001f1ee')
    @commands.guild_only()
    async def serverinfo(self, ctx):
        """gets server id, creation date, etc"""
        seaver = ctx.guild
        now = datetime.utcnow()
        dtcreated = seaver.created_at.strftime('%d %b, %Y %H:%M')
        if now.day == seaver.created_at.day and now.month == seaver.created_at.month and now.year != seaver.created_at.year:
            dtcreated += ' \U0001f382'
        td_created = self.humanize_td(now - seaver.created_at)
        desc = '__Created__: {}\n`{}`'.format(dtcreated, td_created)
        embed = discord.Embed(description=desc, colour=ctx.guild.me.colour.value & 0xFFFFFE, timestamp=datetime.utcnow())
        embed.set_author(name=str(seaver), icon_url=seaver.icon_url_as(static_format='png', size=32), url=seaver.icon_url_as(static_format='png'))
        embed.add_field(name='__Owner__', value=f'{seaver.owner.mention}`{seaver.owner}`')
        embed.add_field(name='__Region__', value=seaver.region)
        bots = sum(m.bot for m in seaver.members)
        member_text = '`{:,}` | `{:,}`<:bot1:721808209395843143><:bot2:721808220234055680>'.format(seaver.member_count, bots)
        embed.add_field(name='__Members__', value=member_text, inline=False)
        embed.add_field(name='__Roles__', value=str(len(seaver.roles) - 1))
        embed.add_field(name='__Text Channels__', value=str(len(seaver.text_channels)))
        embed.add_field(name='__Voice Channels__', value=str(len(seaver.voice_channels)))
        anim_e = sum(1 for e in seaver.emojis if e.animated)
        norm_e = len(seaver.emojis) - anim_e
        emoji_text = '`{1}`/`{0}` emojis\n`{2}`/`{0}` animated'.format(seaver.emoji_limit, norm_e, anim_e)
        embed.add_field(name=f'__# of Emojis__ [{len(seaver.emojis)}]', value=emoji_text)
        boost_text = 'Level `{}` {}\n`{}` boosts, `{:,}` boosters'.format(seaver.premium_tier, '<a:pepeboost:726009263063040030>' * seaver.premium_tier, seaver.premium_subscription_count, len(seaver.premium_subscribers))
        embed.add_field(name='__Server Boosts__', value=boost_text)
        embed.set_footer(text='Server ID: {}'.format(seaver.id), icon_url=seaver.icon_url_as(static_format='png', size=32))
        await ctx.send(embed=embed)

    @reaction_command('\U0001f44c')
    @commands.is_nsfw()
    async def test(self, ctx):
        """test command"""
        m = await ctx.send('send nudes')

    @reaction_command('\U0001f646')
    @commands.guild_only()
    async def someone(self, ctx):
        """get a random user in the server"""
        user = random.choice(ctx.guild.members)
        embed = discord.Embed(title=str(user),
                              color=user.color,
                              description=f'{user.display_name} - {user.mention}')
        embed.set_thumbnail(url=user.avatar_url_as(static_format='png'))
        embed.set_footer(text=f'random member out of {ctx.guild.member_count:,} members')
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Test(bot))
