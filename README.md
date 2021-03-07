# Reaction Commands Extension
Extension to discord.py Bot that adds reaction based commands.


I'll finish this eventually and ~~document it somewhere maybe~~.

[![Documentation Status](https://readthedocs.org/projects/extreactions/badge/?version=latest)](https://extreactions.readthedocs.io/en/latest/?badge=latest)
[![PYPI](https://img.shields.io/pypi/v/ext-reactions)](https://pypi.org/project/ext-reactions/)
[![GitHub last commit](https://img.shields.io/github/last-commit/z03h/ext-reactions?color=2480c0)](https://github.com/z03h/ext-reactions)

😄😄😄😄

```python
# install with pip
python3 -m pip install ext-reactions
# or windows
py -3 -m pip install ext-reactions

# developement install
python3 -m pip install -U git+https://github.com/z03h/ext-reactions@master
# or windows
py -3 -m pip install -U git+https://github.com/z03h/ext-reactions@master
```
___
### Example code

```python
import asyncio

import discord
from discord.ext import commands, reactioncommands

intents = discord.Intents.default()
intents.members = True


bot = reactioncommands.ReactionBot(command_prefix='!',
                                   prefix_emoji='🤔',
                                   listening_emoji='👀',
                                   intents=intents)

@bot.reaction_command('🏓')
async def ping(ctx):
    await ctx.send('Pong!')

with open('definitely-not-my-token', 'r') as f:
    token = f.read()

bot.run(token)
```
___

### Why would you use this?

You wouldn't

~~You can make Bot commands without message intent, so it has that going for it~~
