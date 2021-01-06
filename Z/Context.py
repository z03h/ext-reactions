import discord
from discord.ext import commands


class _ProxyMessage(discord.Message):
    def __init__(self, m_id, author, channel, guild):
        self.id = m_id
        self.author = author
        self.channel = channel
        self.guild = guild
        self._state = author._state


class ReactionContext(commands.Context):
    def __init__(self, bot, message_id, author, channel, guild):
        self.prefix = ''
        self.bot = bot
        self.message = _ProxyMessage(message_id, author, channel, guild)
        self._state = author._state
        self.kwargs = {}

    def set_command(self, command, emoji):
        self.invoked_with = emoji
        self.command = command
        self.args = (command.cog, self) if command.cog else (self,)

    async def reply(self, *args, **kwargs):
        try:
            return await super().reply(*args, **kwargs)
        except discord.NotFound:
            return await self.send(*args, **kwargs)
