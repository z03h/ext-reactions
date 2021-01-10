from discord.ext import commands

__all__ = ('ReactionOnlyCommand',)

class ReactionOnlyCommand(commands.CommandError):
    pass
