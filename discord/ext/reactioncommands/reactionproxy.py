import discord

__all__ = ('ProxyMessage', 'ProxyPayload')

class ProxyBase:
    """Base class for Proxy objects

    Parameters
    ----------
    bot: :class:`Bot <discord.ext.commands.Bot>`
        Your bot instance
    id: :class:`int`
        the id for the object this is proxying

    Attributes
    ----------
    id: :class:`int`
        the id for object this is proxying
    """
    def __init__(self, bot, id):
        self._state = bot._connection
        self.id = id


class ProxyUser(ProxyBase, discord.User):
    """Proxy for :class:`discord.User`"""
    pass


class ProxyMember(ProxyBase, discord.Member):
    """Proxy for :class:`discord.Member`

    Attributes
    ----------
    guild: Union[:class:`discord.Guild`, :class:`~discord.ext.reactioncommands.reactionproxy.ProxyGuild`]
        Guild this proxy member belongs to
    """

    def __init__(self, bot, id, guild):
        super().__init__(bot, id)
        self.guild = guild


class ProxyTextChannel(ProxyBase, discord.TextChannel):
    """Proxy for :class:`discord.TextChannel`

    Attributes
    ----------
    guild: Union[:class:`discord.Guild`, :class:`~discord.ext.reactioncommands.reactionproxy.ProxyGuild`]
        Guild this proxy channel belongs to
    """
    def __init__(self, bot, id, guild):
        super().__init__(bot, id)
        self.guild = guild

class ProxyDMChannel(ProxyBase, discord.DMChannel):
    """Proxy for :class:`discord.DMChannel`

    Attributes
    ----------
    recepient: Union[:class:`discord.User`, :class:`~discord.ext.reactioncommands.reactionproxy.ProxyUser`]
        User this is a DM with
    """

    def __init__(self, bot, id, user):
        super().__init__(bot, id)
        self.recepient = user


class ProxyGuild(ProxyBase, discord.Guild):
    """Proxy class for :class:`discord.Guild`"""
    pass


class ProxyPayload:
    """Class to mimic :class:`discord.RawReactionActionEvent`. Should have all the
    same attributes. Useful for :meth:`.ReactionBot.get_command_emoji` from a
    message.

    Use :meth:`~.ProxyPayload.from_message` to create an instance of this class.

    Some attributes will be  ``None`` since :class:`discord.Message` doesn't
    have those attributes. You can pass them yourself as ``kwargs`` if you use
    :meth:`~.ProxyPayload.from_message`.

    Attributes
    ----------
    user_id: :class:`int`
        user id to represent who this payload comes from
    channel_id: :class:`int`
        channel id to represent where this payload comes from
    guild_id: Optional[:class:`int`]
        guild id to represent where this payload comes from
        or ``None`` for dms
    member: Union[:class:`discord.Member`, :class:`discord.User`]
        From :attr:`discord.Message.author`
    emoji: Any
        ``None`` unless manually passed in
    event_type: Any
        ``None`` unless manually passed in
    """

    def __init__(self, **kwargs):
        self.channel_id = kwargs.get('channel_id')
        self.message_id = kwargs.get('message_id')
        self.guild_id = kwargs.get('guild_id')
        self.emoji = kwargs.get('emoji')
        self.member = kwargs.get('member')
        self.user_id = kwargs.get('user_id')
        self.event_type = kwargs.get('event_type')

    @classmethod
    def from_message(cls, message, *, author=None, emoji=None, event_type=None):
        """Classmethod to create a :class:`.ProxyPayload` from a message.

        Parameters
        ----------
        message: :class:`discord.Message`
            Message to get "payload" from
        author: Union[:class:`discord.User`, :class:`discord.Member`]
            If you want to overwrite ``message.author`` with a different user.
        emoji: Any
            Defaults to ``None``
        event_type: Any
            Defaults to ``None``
        """
        author = author or message.author
        return cls(channel_id=message.channel.id,
                   message_id=message.id,
                   guild_id=getattr(message.guild, 'id', None),
                   member=author,
                   user_id=author.id,
                   emoji=emoji,
                   event_type=event_type
                   )

    @classmethod
    def from_reaction_user(cls, reaction, user, *, event_type=None):
        """Classmethod to create a :class:`.ProxyPayload` from a reaction and user.

        For use with :func:`~discord.on_reacton_add` and
        :func:`~discord.on_reaction_remove`.

        Parameters
        ----------
        reaction: :class:`discord.Reaction`
            Reaction from event
        user: Union[:class:`discord.User`, :class:`discord.Member`]
            The user or member from event
        event_type: Any
            Defaults to ``None``
        """
        return cls.from_message(reaction.message,
                                author=user,
                                emoji=reaction.emoji,
                                event_type=event_type
                                )


class ProxyMessage:
    """Class to mimic :class:`discord.Message`. Not usable like
    :class:`discord.PartialMessage` and only has attributes set.

    .. note::
        Any of these attributes could be a
        :class:`~discord.ext.reactioncommands.reactionproxy.ProxyBase` if they
        cannot be resolved to an object.

    Attributes
    ----------
    id: :class:`int`
        :attr:`payload.message_id <discord.RawReactionActionEvent.message_id>`
    author: Union[:class:`discord.User`, :class:`discord.Member`]
        :attr:`payload.member <discord.RawReactionActionEvent.member>` or
        ``guild.get_member``/``bot.get_user`` on
        :attr:`payload.user_id <discord.RawReactionActionEvent.user_id>`.
    channel: Union[:class:`discord.TextChannel`, :class:`discord.DMChannel`]
        ``bot.get_channel`` on :attr:`payload.channel_id <discord.RawReactionActionEvent.channel_id>`.
    guild: Optional[:class:`discord.Guild`]
        ``bot.get_guild`` on :attr:`payload.guild_id <discord.RawReactionActionEvent.guild_id>`
    """
    def __init__(self, id, author, channel, guild):
        self.id = id
        self.author = author
        self.channel = channel
        self.guild = guild

    @classmethod
    def from_payload(cls, bot, payload):
        """Classmethod to create a :class:`.ProyMessage` from a payload.
        For use with raw reaction methods

        Parameters
        ----------
        bot: :class:`~discord.ext.commands.Bot`
            requires your bot instance for various ``get_x`` methods.
        payload: :class:`discord.RawReactionActionEvent`
            payload from a raw reaction event
        """
        author, channel, guild = bot._create_proxies(payload)
        return cls(payload.message_id, author, channel, guild)

    @classmethod
    def from_reaction_user(cls, reaction, user):
        """Classmethod to create a :class:`.ProxyMessage` from
        a reaction and user. For use with on reaction methods

        Parameters
        ----------
        reaction: :class:`discord.Reaction`
            reaction
        user: Union[:class:`discord.Member`, :class:`discord.User`]
            user
        """
        msg = reaction.message
        return cls(msg.id, user, msg.channel, msg.guild)
