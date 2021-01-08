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
    def __init__(self, bot, message_id, author, channel):
        self.prefix = ''
        self.bot = bot
        self.message = _ProxyMessage(message_id, author, channel, channel.guild)
        self._state = author._state

    def set_command(self, prefix, command, emoji):
        self.prefix = prefix
        self.invoked_with = emoji
        self.command = command
        self.reaction_command = True
