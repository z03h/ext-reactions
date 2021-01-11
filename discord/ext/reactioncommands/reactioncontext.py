import discord
from discord.ext import commands

__all__ = ('ReactionContext',)

class ReactionContext(commands.Context):

    def __init__(self, bot, payload, author, **attrs):
        self.bot = bot
        # bot is the only guarateed thing here
        # since all the proxies get state from bot
        self._state = bot._connection

        self.prefix = attrs.pop('prefix', None)
        self.command = attrs.pop('command', None)
        self.message = attrs.pop('message', None)
        self.args = attrs.pop('args', [])
        self.kwargs = attrs.pop('kwargs', {})
        self.view = attrs.pop('view', None)
        self.invoked_with = attrs.pop('invoked_with', None)
        self.invoked_subcommand = attrs.pop('invoked_subcommand', None)
        self.subcommand_passed = attrs.pop('subcommand_passed', None)
        self.command_failed = attrs.pop('command_failed', False)

        # ReactionContext specific attributes
        self.payload = payload
        self.reaction_command = True
        self.remove_after = []
        self.listening_emoji = None
        self.full_emojis = ''
        # need to separate ctx.author from ctx.message.author
        # since they can be different users
        self.author = author

    async def fetch(self):
        if self.message is None:
            return None
        self.message = await self.message.fetch()
        return self.message

    def get(self):
        if self.message is None:
            return None
        m = self.bot._get_message(self.message.id)
        if m:
            self.message = m
        return m
