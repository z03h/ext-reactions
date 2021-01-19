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

Create a :class:`~.ReactionBot`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    bot = reactioncommands.ReactionBot(prefix, command_emoji, listening_emoji)

- :attr:`~.ReactionBot.command_emoji`: Similar to ``command_prefix`` but for
  reaction commands. Will start a "listening session" where the bot listens for
  raw reaction add/remove with :meth:`~discord.ext.commands.Bot.wait_for` and finds
  the matching command from the emojis added/removed.

- :attr:`~.ReactionBot.listening_emoji` If set, this emoji will be added after
  the user reacts with the :attr:`~.ReactionBot.command_emoji` to let the user know
  the "listening session" has started. Also used for invoking subcommands.

Use decorators to add commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- :meth:`@ReactionBot.reaction_command(emoji) <discord.ext.reactioncommands.ReactionBot.reaction_command>`
- :meth:`@ReactionBot.reaction_group(emoji) <discord.ext.reactioncommands.ReactionBot.reaction_group>`

.. code-block:: python

    @bot.reaction_command("🤔")
    async def something(ctx):
        pass

If you're in a cog

- :func:`@reactioncommands.reaction_command(emoji) <discord.ext.reactioncommands.reaction_command>`
- :func:`@reactioncommands.reaction_group(emoji) <discord.ext.reactioncommands.reaction_group>`.

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
        # ctx.invoked_with will be which emoji(s) the user
        # invoked the command with, so "👋👋" or "👋👋👋".
        await ctx.send(f"{ctx.invoked_with} {ctx.author}")

Groups
~~~~~~

.. code-block:: python

    @bot.reaction_group("👋", invoke_without_command=True)
    async def hi(ctx):
        await ctx.send(f"Hi {ctx.author}")

    @hi.reaction_command("🚶")
    async def bye(ctx):
        await ctx.send(f"Oh! Sorry to see you go {ctx.author} :(")

Mixing :class:`ReactionGroups <.ReactionGroup>` with :class:`Commands <discord.ext.commands.Command>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # can be invoked with messagese or reactions
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
        await ctx.send(f"Send that {ctx.invoked_with} {ctx.author} 👍👍👍")

Anyways, here's a huge wall of example code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Code with comments that explain what some stuff does.

.. code-block:: python

    import asyncio

    import discord
    from discord.ext import commands, reactioncommands

    intents = discord.Intents.default()
    intents.members = True


    # 'prefix ' is the normal command_prefix for message commands.
    # '🤔' is the reaction prefix. It must be added to start listening for command emojis.
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
    # + is add reaction, - is remove reaction
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

    # case_insensitive will try to ignore different skin color/gender modifiers.
    # You can also invoke the subcommand with:
    # +🤔(prefix) > +👍🏾 > +👀(listen for subcommand) > +👍 > -👍
    @bot.reaction_group('👍🏾', case_insensitive=True)
    async def parent(ctx):
        await ctx.send(f'In parent command **{ctx.command}**!\n' \
                       '{ctx.invoked_subcommand.name=}\n' \
                       '{ctx.subcommand_passed=}\n{"-"*10}')

    # invoke_with_message=False means the command can
    # only be invoked from reactions (default is True).
    @parent.reaction_command('👍🏾👍🏾', invoke_with_message=False)
    async def sub(ctx):
        """
        Groups are hard to use with reactions.
        This feature mainly exists to be compatible with normal Groups,
        since reaction commands can be invoked with a message.
        """
        await ctx.send(f'In sub command **{ctx.command}**!\n' \
                       '{ctx.invoked_subcommand=}---{ctx.subcommand_passed=}\n' \
                       '{ctx.command.parent.name=}')


    # Supports checks, cooldowns, max_concurrency,
    # before and after invoke, and local error handlers
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.max_concurrency(1)
    # You can pass a list/tuple of strings to, similar to aliases.
    # This command can be invoked with:
    # +🤔(prefix) > +🥺
    # or
    # +🤔(prefix) > +🥺 > -🥺
    @bot.reaction_command(['🥺', '🥺🥺'])
    async def please(ctx):
        text = 'ctx.message will be a PartialMessageif invoked from reactions\n' \
               'To get a full message, you can use ctx.get() which searches message cache' \
               'or ctx.fetch() which is a shortcut to PartialMessage.fetch()\n'
               'ctx.author is NOT the same as ctx.message.author for reaction commands\n' \
               'ctx.message is the message reactions were added to\n' \
               'ctx.author is the user who added reactions, not message.author\n' \
               'Lots of things broken, ex: args will only be default value or None'
        await ctx.trigger_typing()
        await asyncio.sleep(9)
        await ctx.message.reply(text)


    with open('definitelynotmytoken', 'r') as f:
        token = f.read()
    bot.run(token)
