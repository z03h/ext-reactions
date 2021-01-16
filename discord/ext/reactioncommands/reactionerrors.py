from discord.ext import commands

__all__ = ('ReactionOnlyCommand',)

class ReactionOnlyCommand(commands.CommandError):
    """Subclass of :exc:`~discord.ext.commands.CommandError`. Similar to
    :exc:`~discord.ext.commands.DisabledCommand`. Nothing added here.
    """
    pass
