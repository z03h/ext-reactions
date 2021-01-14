.. currentmodule:: discord

Quickstart
==========

Short Examples
^^^^^^^^^^^^^^

Import
~~~~~~

.. code-block:: python

    from discord.ext import reactioncommands

or specific things

.. code-block:: python

    from discord.ext.reactioncommands import reaction_command, reaction_group

Create bot
~~~~~~~~~~

.. code-block:: python

    bot = reactioncommands.ReactionBot(prefix, command_emoji, listening_emoji)

Use decorators to add commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:meth:`@ReactionBot.reaction_command(emoji) <discord.ext.reactioncommands.ReactionBot.reaction_command>`
or :meth:`@ReactionBot.reaction_group(emoji) <discord.ext.reactioncommands.ReactionBot.reaction_group>`
to create a reaction command. If you're in a cog, use the decorators
:func:`@reactioncommands.reaction_command(emoji) <discord.ext.reactioncommands.reaction_command>` or
:func:`@reactioncommands.reaction_group(emoji) <discord.ext.reactioncommands.reaction_group>`.

.. code-block:: python

    @bot.reaction_command("🤔")
    async def something(ctx):
        pass

or in a cog

.. code-block:: python

    class ReactionCog(commands.Cog):
        @reaction_command("🤔")
        async def something(self, ctx):
            pass


Short-ish code examples
^^^^^^^^^^^^^^^^^^^^^^^

Simple command
~~~~~~~~~~~~~~

.. code-block:: python

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

Cogs
~~~~

.. code-block:: python

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

            await ctx.send(f"🎉🎉 {member.id} 🎉🎉")

    # Don't forget to add setup(bot)

Multiple emojis in the name or emoji aliases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @bot.reaction_command(["👋👋", "👋👋👋"])
    async def hi(ctx):
        # ctx.prefix will be which emoji(s) the user
        # invoked the command with, so 👋👋 or 👋👋👋.
        await ctx.send(f"{ctx.prefix} {ctx.author}")

Groups
~~~~~~

.. code-block:: python

    @bot.reaction_group("👋", invoke_without_command=True)
    async def hi(ctx):
        await ctx.send(f"Hi {ctx.author}")

    @hi.reaction_command("🚶")
    async def bye(ctx):
        await ctx.send(f"Oh! Sorry to see you go {ctx.author} :(")

Mixing :class:`ReactionCommands <discord.ext.reactioncommands.ReactionCommand>` with :class:`Commands <discord.ext.commands.Command>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python


    @bot.reaction_group("👋", invoke_without_command=True)
    async def hi(ctx):
        await ctx.send(f"Hi {ctx.author}")

    # normal command that can only be invoked with a message
    @hi.command()
    async def hihi(ctx):
        await ctx.send(f"HiHiHi there {ctx.author}")

    # reaction command that can only be invoked with reactions
    @hi.reaction_command("🇭🇮", invoke_with_message=False)
    async def _hihi(ctx):
        await ctx.send("🇭🇮 👋")

Case insensitive
~~~~~~~~~~~~~~~~

.. code-block:: python

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
