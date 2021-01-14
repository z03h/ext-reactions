.. currentmodule:: discord.ext

API Reference
=============

Bot
^^^

Bot classes that you can use to add reaction commands.

The default order in which everything is called and what methods call what:

- :func:`on_raw_reaction_add(payload) <discord.on_raw_reaction_add>`

  - :meth:`process_reaction_commands(payload) <.ReactionBot.process_reaction_commands>`

    - :meth:`get_reaction_context(payload) <.ReactionBot.get_reaction_context>`

      - :meth:`reaction_before_processing(ctx) <.ReactionBot.reaction_before_processing>`

    - :meth:`reaction_invoke(ctx) <.ReactionBot.reaction_invoke>`

      - :meth:`reaction_after_processing(ctx) <.ReactionBot.reaction_after_processing>`

      - :meth:`invoke(ctx) <discord.ext.commands.Bot.invoke>` which runs checks,
        before invokes, arg conversion, and all that stuff.

ReactionBotMixin
~~~~~~~~~~~~~~~~

Can use this to add reaction commands for your own bot subclass.

.. autoclass:: discord.ext.reactioncommands.ReactionBotMixin

.. note::
    Probably subclass :class:`.ReactionBot` or :class:`.AutoShardedReactionBot`
    instead.

ReactionBot
~~~~~~~~~~~

.. autoclass:: discord.ext.reactioncommands.ReactionBot
    :members:
    :inherited-members: Bot

AutoShardedReactionBot
~~~~~~~~~~~~~~~~~~~~~~

Woah look at you. Imagine having a bot big enough to use
:class:`.AutoShardedReactionBot`.

.. autoclass:: discord.ext.reactioncommands.AutoShardedReactionBot
    :members:

ReactionCommand
^^^^^^^^^^^^^^^^

ReactionCommand classes and other related stuff. Mostly behave like normal
commands. Only big difference is :attr:`emojis <.ReactionCommand.emojis>`
and altered :meth:`_parse_arguments <.ReactionCommand._parse_arguments>` for
argument parsing.

Decorators
~~~~~~~~~~

Decorators for adding commands in cogs.

.. autodecorator:: discord.ext.reactioncommands.reaction_command

.. autodecorator:: discord.ext.reactioncommands.reaction_group


Command Classes
~~~~~~~~~~~~~~~

.. autoclass:: discord.ext.reactioncommands.ReactionGroupMixin

ReactionCommand
---------------

.. autoclass:: discord.ext.reactioncommands.ReactionCommand
    :members:
    :inherited-members: Command
    :private-members: _parse_arguments

ReactionGroup
-------------

.. autoclass:: discord.ext.reactioncommands.ReactionGroup
    :members:
    :inherited-members: Group
    :private-members: _parse_arguments

ReactionContext
^^^^^^^^^^^^^^^

There's a lot of weird crap that goes on here. A
:class:`ProxyBase <discord.ext.reactioncommands.reactionproxy>` is used if
anything from  :class:`payload <discord.RawReactionActionEvent>`
cannot be resolved to a matching object.

Ex: A :class:`ProxyMember <discord.ext.reactioncommands.reactionproxy.ProxyMember>`
or :class:`ProxyUser <discord.ext.reactioncommands.reactionproxy.ProxyUser>`
may be used instead of :class:`discord.Member` or :class:`discord.User` if
:meth:`~discord.Guild.get_member` or :meth:`~discord.ext.commands.Bot.get_user`
return ``None`` and :attr:`payload.member <discord.RawReactionActionEvent.member>`
is ``None``.

.. autoclass:: discord.ext.reactioncommands.ReactionContext
    :members:
