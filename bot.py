
import discord
from discord.ext import commands

from Z import MyBot
from Z.ReactionCore import reaction_command
from Z.ReactionHelp import ReactionHelp


intents = discord.Intents(members=True, reactions=True,
                          guilds=True, voice_states=True,
                          messages=True)
start_activity = discord.Activity(type=3, name='for \U0001f916')
bot = MyBot.RBot(command_prefix =('zz ', 'zz'),
                 command_emoji='\U0001f916',
                 listening_emoji='\U000025b6\U0000fe0f',
                 intents=intents,
                 case_insensitive=True,
                 max_messages=None,
                 owner_id=162074751341297664,
                 allowed_mentions=discord.AllowedMentions.none(),
                 help_command=ReactionHelp(verify_type=True),
                 activity=start_activity)

bot.load_extension('cogs.test')
bot.load_extension('jishaku')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.reaction_command('\U0001f44b')
async def hi(ctx):
    """says hi lmao"""
    await ctx.send(f'hello there {ctx.author.mention}')

@bot.reaction_command('\U0000267b\U0000fe0f')
@commands.is_owner()
async def reload(ctx):
    """reloads extensions"""
    extensions = bot.extensions.copy()
    for ext in extensions:
        bot.reload_extension(ext)
    await ctx.send("reloaded \U0001f44d")

@bot.reaction_command('\U0000274c')
@commands.is_owner()
async def close(ctx):
    """logs out, goodnight i love you"""
    await ctx.send('Goodnight \U0001f6cf')
    await bot.close()

@bot.event
async def on_command_error(context, exception):
    """overrides bots on_command_error to give some more general error messages"""
    if hasattr(context.command, 'on_error'):
        return
    cog = context.cog
    if cog and cog._get_overridden_method(cog.cog_command_error) is not None:
        return
    await bot.process_command_error(context, exception)

with open('definitelynotmytoken', 'r') as f:
    token = f.read()
bot.run(token)
