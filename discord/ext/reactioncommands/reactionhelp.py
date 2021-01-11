import discord
from discord.ext import commands

from .reactioncore import ReactionCommandMixin
from .reactioncontext import ReactionContext

__all__ = ('ReactionHelp',)


class ReactionHelp(commands.DefaultHelpCommand):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('paginator', commands.Paginator(suffix=None, prefix=None))
        self.emojis = kwargs.get('emojis', ['\U0001f1ed'])
        self.match_command_type = kwargs.get('match_command_type', True)
        super().__init__(*args, **kwargs)

    def get_ending_note(self):
        bot = self.context.bot
        return f"Bot that works with reactions and emojis\n" \
               f"React with {bot.command_emoji} to start a command\n" \
               f"Add reactions to get the command you want. Remove {bot.command_emoji} to start the command"

    def add_indented_commands(self, commands, *, heading, max_size=None):
        if not commands:
            return

        self.paginator.add_line(f'__**{heading}**__')

        def filter_regional(c):
            if 0x1f1e6 <= ord(c) <= 0x1f1ff:
                return c + '\u200b'
            return c

        get_width = discord.utils._string_width

        for command in commands:
            command_emojis = getattr(command, 'emojis', None)
            if command_emojis:
                formatted_emojis = []
                for emoji in command_emojis:
                    formatted_emojis.append(''.join(map(filter_regional, emoji)))
                entry = '{0}{1}=**{2}** {3}'.format(self.indent * '\u200a',
                                                    ','.join(formatted_emojis),
                                                    command.name,
                                                    f'`{command.short_doc}`' if command.short_doc else '')
                self.paginator.add_line(self.shorten_text(entry.strip()))
            else:
                entry = '{0}**{1}** {2}'.format(self.indent * '\u200a',
                                                command.name,
                                                f'`{command.short_doc}`' if command.short_doc else '')
                self.paginator.add_line(self.shorten_text(entry))

    async def filter_commands(self, commands, *, sort=False, key=None):
        if self.match_command_type:
            reaction_command = getattr(self.context, 'reaction_command', False)
            if reaction_command:
                cmds = (cmd for cmd in commands if isinstance(cmd, ReactionCommandMixin))
            else:
                cmds = (cmd for cmd in commands if getattr(cmd, 'invoke_with_message', True))
        return await super().filter_commands(cmds, sort=sort, key=key)

    def _add_to_bot(self, bot):
        command = _ReactionHelpCommandImpl(self, **self.command_attrs)
        bot.add_command(command)
        self._command_impl = command

    def _remove_from_bot(self, bot):
        bot.remove_command(self._command_impl.name)
        self._command_impl._eject_cog()
        self._command_impl = None

class _ReactionHelpCommandImpl(ReactionCommandMixin, commands.help._HelpCommandImpl):

    def __init__(self, inject, *args, **kwargs):
        kwargs['emojis'] = inject.emojis
        super().__init__(inject, *args, **kwargs)
