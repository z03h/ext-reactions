# Reaction Command extension
Extension to discord.py Bot that adds reaction commands.


I'll finish this eventually and ~~document it somewhere maybe~~.
[Nice, docs are here](https://extreactions.readthedocs.io/en/latest/) 😄
[![Documentation Status](https://readthedocs.org/projects/extreactions/badge/?version=latest)](https://extreactions.readthedocs.io/en/latest/?badge=latest)

___
Example code

```python
import asyncio

import discord
from discord.ext import commands, reactioncommands

intents = discord.Intents.default()
intents.members = True


# 'prefix ' is the normal command_prefix for message commands.
# '🤔'' is the reaction prefix. It must be added to start listening for command emojis.
# A user can only have 1 listening session at once.
# If they mess up the command they must end the session by removing
# 🤔(reaction prefix) and adding the reaction prefix again.
# '👀' will be added to let the user know the bot is listening for
# reaction events and for separating groups from subcommands.
bot = reactioncommands.ReactionBot('prefix ', '🤔', '👀',
                                   intents=intents)
# command_emoji and listening_emoji support callables like `get_emoji_prefix(bot, payload)`
# All the normal Bot kwargs will work also.



# To invoke this command you would react 🤔 on a message.
# The bot will add 👀, then you can add reactions to invoke the command.
# '👋👋' is what needs to be added/removed to invoke this command.
# In total, you would follow this reaction order:
# `+` is add reaction, `-` is remove reaction
# +🤔(prefix) > +👋 > -👋
@bot.reaction_command('👋👋', name='hi')
async def not_hi(ctx):
    """Says hi!"""
    await ctx.send(f'Hi {ctx.author.mention}!')
# You can also invoke this with a message with content 'prefix hi'.
# Works with normal @commands.command() kwargs.



# Groups works too!
# To invoke the subcommand 'sub', you could react:
# +🤔(prefix) > +👍🏾 > +👀(listen for subcommand) > -👍🏾 > +👍🏾
# 👀 (listening_emoji) separates parent reactions from subcommand reactions

# `case_insensitive` will try to ignore different skin color/gender modifiers.
# You can also invoke the subcommand with:
# +🤔(prefix) > +👍🏾 > +👀(listen for subcommand) > +👍 > -👍
@bot.reaction_group('👍🏾', case_insensitive=True)
async def parent(ctx):
    await ctx.send(f'In parent command **{ctx.command}**!\n' \
                   '{ctx.invoked_subcommand.name=}\n' \
                   '{ctx.subcommand_passed=}\n{"-"*10}')

# `invoke_with_message=False` means the command can
# only be invoked from reactions (default is True).
@parent.reaction_command('👍🏾👍🏾', invoke_with_message=False)
async def sub(ctx):
    """
    Groups are hard to use with reactions.
    This feature mainly exists to be compatible with normal Groups,
    since reaction commands can be invoked with a message.
    """
    await ctx.send(f'In sub command **{ctx.command}**!\n' \
                   '`{ctx.invoked_subcommand=}`---`{ctx.subcommand_passed=}`\n' \
                   '{ctx.command.parent.name=}')



# Supports checks, cooldowns, max_concurrency,
# before and after invoke, and local error handlers
@commands.guild_only()
@commands.cooldown(1, 60, commands.BucketType.user)
@commands.max_concurrency(1)
# You can pass a list/tuple of strings to function as aliases.
# This command can be invoked with:
# +🤔(prefix) > +🥺
# or
# +🤔(prefix) > +🥺 > -🥺
@bot.reaction_command(['🥺', '🥺🥺'])
async def please(ctx):
    text = 'ctx.message will be a PartialMessage\n' \
           'To get a full message, you can use `ctx.get()` which searches message cache' \
           'or `ctx.fetch()` which is a shortcut to `PartialMessage.fetch()\n`'
           f'{ctx.author=} is **NOT** the same as ctx.message.author for reaction commands\n' \
           'ctx.message is the message reactions were added to\n' \
           'ctx.author is the user who added reactions, not the author of the message\n' \
           'Lots of things broken, ex: args will only be default value or None, lmao'
    await ctx.trigger_typing()
    await asyncio.sleep(9)
    await ctx.message.reply(text)


with open('definitelynotmytoken', 'r') as f:
    token = f.read()
bot.run(token)

```
___

Why would you use this?

You wouldn't, but you can use/subclass `ReactionBot` and it should behave
like a normal `ext.commands.Bot`.

~~You can make Bot commands without message intent, so it has that going for it~~
