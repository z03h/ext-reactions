import discord
from discord.ext import commands


class ReactionCommand(commands.Command):
    def __init__(self, emojis, func, *args, **kwargs):
        super().__init__(func, *args, **kwargs)
        self.emojis = [emojis] if isinstance(emojis, str) else emojis
    async def prepare(self, ctx):
        return

    def copy(self):
        ret = self.__class__(self.emojis, self.callback, **self.__original_kwargs__)
        return self._ensure_assignment_on_copy(ret)

def reaction_command(emoji, name=None, cls=None, **attrs):
    if cls is None:
        cls = ReactionCommand

    def decorator(func):
        if isinstance(func, commands.Command):
            raise TypeError('Callback is already a command.')
        return cls(emoji, func, name=name, **attrs)

    return decorator
