
import discord
from discord.ext import commands

from Z import ReactionBot, Context
from Z.ReactionCommand import reaction_command


intents = discord.Intents(members=True, reactions=True,
                          guilds=True, voice_states=True)
start_activity = discord.Activity(type=3, name='for \U0001f916')
bot = ReactionBot.ReactionBotBase(command_emoji='\U0001f916',
                                  listening_emoji='\U000025b6\U0000fe0f',
                                  intents=intents,
                                  max_messages=None,
                                  owner_id=162074751341297664,
                                  activity=start_activity)
bot.load_extension('cogs.test')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command('\U0001f44b')
async def hi(ctx):
    """says hi lmao"""
    await ctx.send(f'hello there {ctx.author.mention}')

@bot.command('\U0000267b\U0000fe0f')
@commands.is_owner()
async def reload(ctx):
    """reloads extensions"""
    extensions = bot.extensions.copy()
    for ext in extensions:
        bot.reload_extension(ext)
    await ctx.send("reloaded \U0001f44d")

@bot.command('\U0000274c')
@commands.is_owner()
async def close(ctx):
    """logs out, goodnight i love you"""
    await ctx.send('Goodnight \U0001f6cf')
    await bot.close()

with open('definitelynotmytoken', 'r') as f:
    token = f.read()
bot.run(token)
