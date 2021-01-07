import discord
from discord.ext import commands

from .Context import ReactionContext


class ReactionCommand(commands.Command):
    def __init__(self, func, *args, **kwargs):
        super().__init__(func, *args, **kwargs)
        emojis = kwargs.get('emojis')
        if not emojis:
            raise ValueError(f'Emojis cannot be empty for {self.name}')
        self.emojis = [emojis] if isinstance(emojis, str) else emojis

    async def prepare(self, ctx):
        if isinstance(ctx, ReactionContext):
            ctx.command = self
            if not await self.can_run(ctx):
                raise CheckFailure('The check functions for command {0.qualified_name} failed.'.format(self))
            self._prepare_cooldowns(ctx)

            if self._max_concurrency is not None:
                await self._max_concurrency.acquire(ctx)
            return await self.call_before_hooks(ctx)
        return await super().prepare(ctx)

def reaction_command(emoji, name=None, cls=None, **attrs):
    if cls is None:
        cls = ReactionCommand

    def decorator(func):
        if isinstance(func, commands.Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, emojis=emoji, **attrs)

    return decorator
