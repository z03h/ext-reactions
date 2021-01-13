.. currentmodule discord

Example code too long, didn't read
==================================

Quickstart

TL;DR

Simple command::

    from discord.ext import reactioncommands

    bot = reactioncommands.ReactionBot(command_prefix="!",
                                       command_emoji="🤔"),
                                       listening_emoij="👀",
                                       listen_timeout=30
                                       )
    @bot.reaction_command("👋")
    async def hi(ctx):
        await ctx.send(f"Hi {ctx.author}")

    # Don't forget bot.run(TOKEN)

Cogs::

    import discord
    from discord.ext import commands, reactioncommands

    class MyCog(commands.Cog):

        def __init__(self, bot):
            self.bot = bot

        @reactioncommands.reaction_command("🎉")
        @commands.guild_only()
        async def tada(self, ctx, member:discord.Member):
            # member will always be None when
            # invoked from reactions.
            member = member or ctx.author

            await ctx.send(f"🎉 Tada 🎉")

    # Don't forget to add setup(bot)

Multiple emojis in the name or emoji aliases::

    @bot.reaction_command(["👋👋", "👋👋👋"])
    async def hi(ctx):
        # ctx.prefix will be which emoji(s) the user
        # invoked the command with, so 👋👋 or 👋👋👋.
        await ctx.send(f"{ctx.prefix} {ctx.author}")

Groups::

    @bot.reaction_group("👋", invoke_without_command=True)
    async def hi(ctx):
        await ctx.send(f"Hi {ctx.author}")

    @hi.reaction_command("🚶")
    async def bye(ctx):
        await ctx.send(f"Oh! Sorry to see you go {ctx.author} :(")

Mixing :class:`ReactionCommands <discord.ext.reactioncommands.ReactionCommand>`
with :class:`Commands <discord.ext.commands.Command>`::

    @bot.reaction_group("👋", invoke_without_command=True)
    async def hi(ctx):
        await ctx.send(f"Hi {ctx.author}")

    # normal command that can only be invoked with a message
    @hi.command()
    async def hihi(ctx):
        await ctx.send(f"HiHiHi there {ctx.author}")

Case insensitive::

    from discord.ext import reactioncommands

    bot = reactioncommands.ReactionBot(command_prefix="!",
                                       command_emoji="🤔"),
                                       listening_emoij="👀",
                                       case_insensitive=True
                                       )

    # can be invoked with any of 👍,👍🏻,👍🏼,👍🏽,👍🏾,👍🏿
    @bot.reaction_command("👍")
    async def hi(ctx):
        await ctx.send(f"Send that {ctx.prefix} {ctx.author} 👍👍👍")
