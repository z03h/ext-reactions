.. currentmodule:: discord

Proxy Objects
=============

You *can* make these yourself if you want, but you probably should avoid it.
These are pretty crap and literally just set :attr:`.ProxyBase.id` and ``_state``.

These exist to try and fill in gaps between :class:`discord.RawReactionActionEvent`
and :class:`discord.Message`.

Stuff like ``ProxyUser.send()`` should work, but ``ProxyUser.name`` will error.

ProxyBase
^^^^^^^^^

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyBase
    :members:

Proxy Subclasses
~~~~~~~~~~~~~~~~

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyUser
    :members:
    :inherited-members: User

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyMember
    :members:
    :inherited-members: Member

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyTextChannel
    :members:
    :inherited-members: TextChannel

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyDMChannel
    :members:
    :inherited-members: DMChannel

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyGuild
    :members:
    :inherited-members: Guild
