import discord


class ProxyBase:

    def __init__(self, bot, id):
        self._state = bot._connection
        self.id = id


class ProxyUser(ProxyBase, discord.User):
    pass


class ProxyMember(ProxyBase, discord.Member):

    def __init__(self, bot, id, guild):
        super().__init__(bot, id)
        self.guild = guild


class ProxyTextChannel(ProxyBase, discord.TextChannel):

    def __init__(self, bot, id, guild):
        super().__init__(bot, id)
        self.guild = guild

class ProxyDMChannel(ProxyBase, discord.DMChannel):

    def __init__(self, bot, id, user):
        super().__init__(bot, id)
        self.recepient = user


class ProxyGuild(ProxyBase, discord.Guild):
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
