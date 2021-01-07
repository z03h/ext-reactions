import discord
from discord.ext import commands

from .ReactionCommand import ReactionCommand
from .Context import ReactionContext

class ReactionHelp(commands.DefaultHelpCommand):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('paginator', commands.Paginator(suffix=None, prefix=None))
        self.emojis = kwargs.get('emojis', '\U0001f1ed')
        super().__init__(*args, **kwargs)

    def get_ending_note(self):
        bot = self.context.bot
        return f"Bot that only works with emojis\n" \
               f"React with {bot.command_emoji} to start \n" \
               f"Add reactions to get the command you want. Remove {bot.command_emoji} to end the timer early"

    def add_indented_commands(self, commands, *, heading, max_size=None):
        if isinstance(self.context, ReactionContext):
            commands = [cmd for cmd in commands if isinstance(cmd, (ReactionCommand,_ReactionHelpCommandImpl))]

        if not commands:
            return

        self.paginator.add_line(f'__**{heading}**__')

        def filter_regional(c):
            if 0x1f1e6 <= ord(c) <= 0x1f1ff:
                return c + '\u200b'
            return c

        get_width = discord.utils._string_width

        for command in commands:
            if isinstance(command, (ReactionCommand, _ReactionHelpCommandImpl)):
                formatted_emojis = []
                for emoji in command.emojis:
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

    async def command_callback(self, ctx, *, command=None):
        if command:
            await self.prepare_help_command(ctx, None)
            bot = ctx.bot

            mapping = self.get_bot_mapping()
            return await self.send_bot_help(mapping)
        else:
            return await super().command_callback(ctx, command=command)

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
        if not isinstance(ctx, ReactionContext):
            return await super().prepare(ctx)
        self._injected = injected = self._original.copy()
        injected.context = ctx
        self.callback = injected.command_callback

        on_error = injected.on_help_command_error
        if not hasattr(on_error, '__help_command_not_overriden__'):
            if self.cog is not None:
                self.on_error = self._on_error_cog_implementation
            else:
                self.on_error = on_error
        ctx.command = self
        if not await self.can_run(ctx):
            raise CheckFailure('The check functions for command {0.qualified_name} failed.'.format(self))
        self._prepare_cooldowns(ctx)

        if self._max_concurrency is not None:
            await self._max_concurrency.acquire(ctx)
        await self.call_before_hooks(ctx)

    def copy(self):
        ret = self.__class__(self.callback, **self.__original_kwargs__)
        return self._ensure_assignment_on_copy(ret)
