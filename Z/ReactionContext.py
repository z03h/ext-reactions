import discord
from discord.ext import commands


class _ProxyMessage(discord.PartialMessage):
    def __init__(self, m_id, author, channel, guild):
        self.id = m_id
        self.author = author
        self.channel = channel
        self.guild = guild
        self._state = author._state


class ReactionContext(commands.Context):
    def __init__(self, bot, payload, author, channel):
        self.prefix = ''
        self.bot = bot
        self.payload = payload
        self.message = _ProxyMessage(payload.message_id, author, channel, channel.guild)
        self._state = author._state
        self.reaction_command = True
        self.remove_after = []
        self.command = None
        self.prefix = None
        self.invoked_with = None
