import discord
from discord.ext import commands


class ReactionHelp(commands.DefaultHelpCommand):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('paginator', commands.Paginator(suffix=None, prefix=None))
        self.emojis = kwargs.get('emojis', '\U0001f1ed')
        super().__init__(*args, **kwargs)

    def get_ending_note(self):
        bot = self.context.bot
        return f"Bot that only works with emojis\n" \
               f"React with {bot.command_emoji} to start listening\n" \
               f"Add reactions to get the command you want. React {bot.command_emoji} to end the timer early"

    def add_indented_commands(self, commands, *, heading, max_size=None):
        if not commands:
            return

        self.paginator.add_line(f'__**{heading}**__')
        max_size = max_size or self.get_max_size(commands)

        get_width = discord.utils._string_width
        for command in commands:
            name = command.name
            width = max_size - (get_width(name) - len(name))
            entry = '{0}{1}={2 {3}'.format(self.indent * '\u200a',
                                                    ','.join('\u200b'.join(emoji) for emoji in command.emojis),
                                                    name,
                                                    f'`{command.short_doc}`' if command.short_doc else '')
            self.paginator.add_line(self.shorten_text(entry.strip()))

    async def command_callback(self, ctx):
        await self.prepare_help_command(ctx, None)
        bot = ctx.bot

        mapping = self.get_bot_mapping()
        return await self.send_bot_help(mapping)

    def copy(self):
        obj = self.__class__(*self.__original_args__, **self.__original_kwargs__)
        obj._command_impl = self._command_impl
        return obj

    def _add_to_bot(self, bot):
        command = _ReactionHelpCommandImpl(self, **self.command_attrs)
        bot.add_command(command)
        self._command_impl = command

    def _remove_from_bot(self, bot):
        bot.remove_command(self._command_impl.name)
        self._command_impl._eject_cog()
        self._command_impl = None

class _ReactionHelpCommandImpl(commands.help._HelpCommandImpl):
    def __init__(self, inject, *args, **kwargs):
        super().__init__(inject, *args, **kwargs)
        self.emojis = [inject.emojis] if isinstance(inject.emojis, str) else inject.emojis

    async def prepare(self, ctx):
        self._injected = injected = self._original.copy()
        injected.context = ctx
        self.callback = injected.command_callback

        on_error = injected.on_help_command_error
        if not hasattr(on_error, '__help_command_not_overriden__'):
            if self.cog is not None:
                self.on_error = self._on_error_cog_implementation
            else:
                self.on_error = on_error

    def copy(self):
        ret = self.__class__(self.emojis, self.callback, **self.__original_kwargs__)
        return self._ensure_assignment_on_copy(ret)
