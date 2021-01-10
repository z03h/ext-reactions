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
