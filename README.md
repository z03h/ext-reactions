# Reaction Command Bot
Bot that can listen to reactions for commands.


I'll finish this eventually and document it somewhere maybe.
___
Example code

```python
import asyncio

import discord
from discord.ext import commands, reactioncommands

intents = discord.Intents.default()
intents.members = True

# 🤔 is the reaction prefix, must be added to start listening for command emojis.
# A user can only have 1 listening session at once.
# If they mess up the command they must end the session then react the reaction prefix again.
# 👀 will be added to let the user know the bot is listening and
# for separating groups from subcommands.
bot = reactioncommands.ReactionBot('prefix ', '🤔', '👀',
                                   intents=intents)
# All the normal Bot kwargs will work also.

# To invoke this command you would react 🤔 on a message.
# The bot will add 👀, then you can add reactions to invoke the command.
# '👋👋'' is what needs to be added/removed to invoke this command.
# In total, you would follow this reaction order:
# `+` is add reaction, `-` is remove reaction
# +🤔(prefix) > +👋 > -👋

# You can also invoke this with a message with content 'prefix hi'.

# Works with normal @commands.command() kwargs.
@bot.reaction_command('👋👋', name='hi')
async def not_hi(ctx):
    """Says hi!"""
    await ctx.send(f'Hi {ctx.author.mention}!')

# Groups works too!
# To invoke the subcommand 'sub', you could react:
# +🤔(prefix) > +👍🏾 > +👀 > -👍🏾 > +👍🏾
# 👀 (listening_emoji) separates parent emojis from subcommand emojis

# `case_insensitive` will try to ignore different skin color/gender emojis.
# You can also invoke the subcommand with:
# +🤔(prefix) > +👍 > +👀 > -👍 > +👍
@bot.reaction_group('👍🏾', case_insensitive=True):
async def parent(ctx):
    await ctx.send(f'In parent command {ctx.command}!\n{ctx.invoked_subcommand=} : {ctx.subcommand_passed=}')

# `invoke_with_message=False` means the command can
# only be invoked from reactions (defaults to True).
@parent.reaction_command('👍🏾👍🏾', invoke_with_message=False):
async def sub(ctx):
    """
    Groups are probably too confusing to use with reactions.
    This mainly exists to be compatible with normal Groups.
    """
    await ctx.send(f'In sub command {ctx.command}!\n{ctx.invoked_subcommand=} : {ctx.subcommand_passed=}\n{ctx.parent=}')

# Supports checks, before and after invoke,  local error handlers,
# cooldowns, and max_concurrency!
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
    text = f'{ctx.author=} is **NOT** the same as ctx.message.author for commands invoked with reactions\n' \
            'ctx.message is the message reactions were added to\n' \
            'ctx.author is the user who added the reactions\n' \
            'If the message is in the cache, ctx.message will be a full message.' \
            'If the message isn\'t in the cache, it will be a PartialMessage\n' \
            'Lots of other shortcomings of context from reactions.'
    await ctx.trigger_typing()
    await asyncio.sleep(9)
    await ctx.message.reply(text)

```
___

Why would you use this?

You wouldn't, but you can use/subclass `ReactionBot` and it should behave like a normal `ext.commands.Bot`.

~~You can make Bot commands without message intent, so it has that going for it~~
