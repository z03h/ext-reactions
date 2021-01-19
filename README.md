# Reaction Commands Extension
Extension to discord.py Bot that adds reaction based commands.


I'll finish this eventually and ~~document it somewhere maybe~~.

[![Documentation Status](https://readthedocs.org/projects/extreactions/badge/?version=latest)](https://extreactions.readthedocs.io/en/latest/?badge=latest)
[Nice, docs are here](https://extreactions.readthedocs.io/en/latest/) 😄

[![PYPI](https://img.shields.io/pypi/v/ext-reactions.svg)](https://pypi.org/project/ext-reactions/) 😄
___
Example code

```python
import asyncio

import discord
from discord.ext import commands, reactioncommands

intents = discord.Intents.default()
intents.members = True


bot = reactioncommands.ReactionBot(command_prefix='!',
                                   command_emoji='🤔',
                                   listening_emoji='👀',
                                   intents=intents)

@bot.reaction_command('🏓')
async def ping(ctx):
    await ctx.send('Pong!')

with open('definitelynotmytoken', 'r') as f:
    token = f.read()

bot.run(token)
```
___

Why would you use this?

You wouldn't, but you can use/subclass `ReactionBot` and it should behave
like a normal `ext.commands.Bot`.

~~You can make Bot commands without message intent, so it has that going for it~~
