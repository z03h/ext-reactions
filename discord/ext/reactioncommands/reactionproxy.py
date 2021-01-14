import discord


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
    guild: Union[:class:`discord.Guild`, :class:`.ProxyGuild`]
        Guild this proxy member belongs to
    """

    def __init__(self, bot, id, guild):
        super().__init__(bot, id)
        self.guild = guild


class ProxyTextChannel(ProxyBase, discord.TextChannel):
    """Proxy for :class:`discord.TextChannel`

    Attributes
    ----------
    guild: Union[:class:`discord.Guild`, :class:`.ProxyGuild`]
        Guild this proxy channel belongs to
    """
    def __init__(self, bot, id, guild):
        super().__init__(bot, id)
        self.guild = guild

class ProxyDMChannel(ProxyBase, discord.DMChannel):
    """Proxy for :class:`discord.DMChannel`

    Attributes
    ----------
    recepient: Union[:class:`discord.User`, :class:`..ProxyUser`]
        User this is a DM with
    """

    def __init__(self, bot, id, user):
        super().__init__(bot, id)
        self.recepient = user


class ProxyGuild(ProxyBase, discord.Guild):
    """Proxy class for :class:`discord.Guild`"""
    pass


class MessagePayload:

    def __init__(self, **kwargs):
        self.channel_id = kwargs.get('channel_id')
        self.message_id = kwargs.get('message_id')
        self.guild_id = kwargs.get('guild_id')
        self.emoji = kwargs.get('emoji')
        self.member = kwargs.get('member')
        self.user_id = kwargs.get('user_id')
        self.event_type = kwargs.get('event_type')

    @classmethod
    def from_message(cls, message):
        author = message.author
        return cls(channel_id=message.channel.id,
                   message_id=message.id,
                   guild_id=getattr(message.guild, 'id', None),
                   member=author,
                   user_id=author.id
                   )


class PayloadMessage:

    def __init__(self, id, author, channel, guild):
        self.id = id
        self.author = author
        self.channel = channel
        self.guild = guild

    @classmethod
    def from_payload(cls, bot, payload):
        author, channel, guild = bot._create_proxies(payload)
        return cls(payload.message_id, author, channel, guild)
