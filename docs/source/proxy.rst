.. currentmodule:: discord

Proxy Objects
=============

You *can* make these yourself if you want, but you probably should avoid it.
These are pretty crap and literally just set :attr:`.ProxyBase.id` and ``_state``.

These exist to try and fill in gaps between :class:`discord.RawReactionActionEvent`
and :class:`discord.Message`.

Methods such as ``ProxyUser.send()`` should work, but attributes such as
``ProxyUser.name`` will error.

Proxy Base
^^^^^^^^^^

Just has :attr:`.ProxyBase.id` and ``_state`` set.

.. autoclass:: discord.ext.reactioncommands.reactionproxy.ProxyBase
    :members:

Subclassed proxies
------------------

.. automodule:: discord.ext.reactioncommands.reactionproxy
    :members:
    :exclude-members: ProxyBase
    :show-inheritance:
