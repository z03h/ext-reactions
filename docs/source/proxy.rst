.. currentmodule:: discord

Proxy Objects
=============

.. autoclass :: discord.ext.reactioncommands.ProxyPayload
    :members:

.. autoclass:: discord.ext.reactioncommands.ProxyMessage
    :members:

Proxy Bases
^^^^^^^^^^^

Just has :attr:`.ProxyBase.id` and ``_state`` set.

.. Warning ::
    You *can* make these yourself if you want, but you probably should avoid.
    These are pretty crap and literally just set :attr:`.ProxyBase.id` and ``_state``,
    and *maybe* some other attributes like :attr:`.ProxyMember.guild` but those
    could also be :class:`.ProxyBase`.

    These exist to try and fill in any gaps between
    :class:`discord.RawReactionActionEvent` and :class:`discord.Message`.

    Methods such as ``ProxyUser.send()`` should work, but attributes such as
    ``ProxyUser.name`` will error.

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyBase
    :members:

Subclassed proxies
------------------

All of these should behave similar to :class:`discord.PartialMessage` except
attributes aren't filled out. Only methods should really work.

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyUser
    :members:
    :show-inheritance:

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyMember
    :members:
    :show-inheritance:

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyTextChannel
    :members:
    :show-inheritance:

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyDMChannel
    :members:
    :show-inheritance:

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyGuild
    :members:
    :show-inheritance:
