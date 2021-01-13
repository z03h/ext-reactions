.. currentmodule discord

ReactionCommand Reference
=========================

ReactionCommand classes and other related stuff.

Decorators
~~~~~~~~~~

Decorators for adding commands in cogs.

.. autodecorator:: discord.ext.reactioncommands.reaction_command

.. autodecorator:: discord.ext.reactioncommands.reaction_group


Command Classes
~~~~~~~~~~~~~~~

ReactionCommand
^^^^^^^^^^^^^^^

.. autoclass:: discord.ext.reactioncommands.ReactionCommand
    :members:
    :inherited-members: Command
    :private-members: _parse_arguments

ReactionGroup
^^^^^^^^^^^^^

.. autoclass:: discord.ext.reactioncommands.ReactionGroup
    :members:
    :inherited-members: Group
    :private-members: _parse_arguments
