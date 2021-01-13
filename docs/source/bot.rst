.. currentmodule discord

Bot Reference
=============

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
^^^^^^^^^^^^^^^^

.. autoclass:: discord.ext.reactioncommands.ReactionBotMixin

.. note::
    Probably use :class:`.ReactionBot` or :class:`.AutoShardedReactionBot`.

ReactionBot
^^^^^^^^^^^

.. autoclass:: discord.ext.reactioncommands.ReactionBot
    :members:
    :inherited-members: Bot

AutoShardedReactionBot
^^^^^^^^^^^^^^^^^^^^^^

Woah look at you bigshot. Imagine having a bot big enough to use
:class:`.AutoShardedReactionBot` and looking at this :o

.. autoclass:: discord.ext.reactioncommands.AutoShardedReactionBot
    :members:
