import re

import discord
from discord.ext import commands

from .reactioncore import ReactionCommandMixin
from .reactioncontext import ReactionContext

__all__ = ('ReactionHelp',)


class ReactionHelp(commands.DefaultHelpCommand):
    """Help command for reaction commands and normal commands. Subclassed from
    :class:`~discord.ext.commands.DefaultHelpCommand`.

    Refer to normal help command guides.

    You can make use of :attr:`ReactionCommand.emojis` for which emojis that can
    invoke a command, :attr:`ReactionContext.reaction_command` to know if help was
    invoked from reactions or a message, and ``isinstance(cmd, ReactionCommandMixin)``
    to check if a command is a :class:`ReactionCommand` or similar.

    Attributes
    ----------
    emojis: Union[:class:`str`, list]
        String or list of strings for emojis to invoke the help command with.
        Defaults to ``['🇭']``.
    match_command_type: :class:`bool`
        Whether commands should be also be filtered based on if help command
        was invoked from reactions or messages.

        Only show reaction commands from reaction invoke, only show commands that
        can be invoked from a message from message invoke.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('paginator', commands.Paginator(suffix=None, prefix=None))
        self.emojis = kwargs.get('emojis', ['\U0001f1ed'])
        self.match_command_type = kwargs.get('match_command_type', True)
        self.regional_pattern = re.compile('[\U0001f1e6-\U0001f1ff]')

        super().__init__(*args, **kwargs)

    def filter_regional(self, emojis):
        """Helper method that uses regex to sub in '\\\\u200b' to prevent regional
        indicators from forming flags but not splitting multi char emojis.

        Parameters
        ----------
        emojis: :class:`str`
            The emojis to split regional indicators

        Returns
        -------
        :class:`str`
            The input with '\\\\u200b' added in
        """
        return self.regional_pattern.sub('\\g<0>\u200b', emojis)

    def get_ending_note(self):
        """Modified to show different text based on reaction or message invoke"""
        ctx = self.context
        if not ctx.prefix:
            return ''
        if getattr(ctx, 'reaction_command', False):
            return "Bot that works with reactions and emojis"\
                   f"React with {ctx.prefix} to start a command\n" \
                   "Add reactions to get the command you want.\n" \
                   f"Remove {ctx.prefix} to start the command"
        else:
            command_name = self.invoked_with
            return "Type {0}{1} command for more info on a command.\n" \
                   "You can also type {0}{1} category for more info on a category.".format(self.clean_prefix, command_name)

    def get_command_signature(self, command):
        """Modified to add :attr:`ReactionCommand.emojis` to the signature
        if command is a :class:`ReactionCommand`
        """
        parent = command.full_parent_name
        alias = command.name if not parent else parent + ' ' + command.name
        prefix = '' if getattr(self.context, "reaction_command", False) else self.clean_prefix

        if getattr(command, "emojis", []):
            emojis = ','.join(map(self.filter_regional, command.emojis)) +'\n'
        else:
            emojis = ''
        return '%s%s%s %s' % (emojis, prefix, alias, command.signature)

    def add_indented_commands(self, commands, *, heading, max_size=None):
        """Modified to also show :attr:`ReactionCommand.emojis`"""
        if not commands:
            return

        self.paginator.add_line(f'__**{heading}**__')

        get_width = discord.utils._string_width

        for command in commands:
            command_emojis = getattr(command, 'emojis', None)
            if command_emojis:
                emojis = ','.join(map(self.filter_regional, command.emojis))
                entry = '{0}{1} | **{2}** {3}'.format(self.indent * '\u200a',
                                                      emojis,
                                                      command.name,
                                                      f'`{command.short_doc}`' if command.short_doc else '')
                self.paginator.add_line(self.shorten_text(entry.strip()))
            else:
                entry = '{0}**{1}** {2}'.format(self.indent * '\u200a',
                                                command.name,
                                                f'`{command.short_doc}`' if command.short_doc else '')
                self.paginator.add_line(self.shorten_text(entry))

    async def filter_commands(self, commands, *, sort=False, key=None):
        """Modified to also filter :attr:`ReactionHelp.match_command_type`."""
        if self.match_command_type:
            if getattr(self.context, 'reaction_command', False):
                commands = (cmd for cmd in commands if isinstance(cmd, ReactionCommandMixin))
            else:
                commands = (cmd for cmd in commands if getattr(cmd, 'invoke_with_message', True))
        return await super().filter_commands(commands, sort=sort, key=key)

    def get_bot_mapping(self):
        """Same as :meth:`~discord.ext.commands.HelpCommand.get_bot_mapping`.

        :meta private:
        """
        bot = self.context.bot
        mapping = {}
        for command in bot.commands:
            mapping.setdefault(command.cog, []).append(command)
        return mapping

    async def command_callback(self, ctx, *, command=None):
        """Nothing changed if help was invoked from a message.

        .. note::
            If invoked from reactions, modified to use :attr:`ReactionContext.full_emojis`
            as command input so you can get help for specific commands with reactions.

            Uses the same method of invoking subcommands to get help for a specific
            command. Add the emojis after :attr:`ReactionHelp.emojis` and
            :attr:`~ReactionBot.listening_emoji`.
        """
        if getattr(ctx, 'reaction_command', 'False'):
            command = ctx.full_emojis.strip().partition(' ')[2] or None
            await self.prepare_help_command(ctx, command)
            bot = ctx.bot

            if command is None:
                mapping = self.get_bot_mapping()
                return await self.send_bot_help(mapping)
            keys = command.split(' ')
            cmd = bot.get_reaction_command(keys[0])
            if cmd is None:
                string = await maybe_coro(self.command_not_found, self.remove_mentions(keys[0]))
                return await self.send_error_message(string)

            for key in keys[1:]:
                try:
                    found = cmd.get_reaction_command(key)
                except AttributeError:
                    string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                    return await self.send_error_message(string)
                else:
                    if found is None:
                        string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                        return await self.send_error_message(string)
                    cmd = found
            if isinstance(cmd, commands.Group):
                return await self.send_group_help(cmd)
            else:
                return await self.send_command_help(cmd)
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

class _ReactionHelpCommandImpl(ReactionCommandMixin, commands.help._HelpCommandImpl):

    def __init__(self, inject, *args, **kwargs):
        kwargs['emojis'] = inject.emojis
        super().__init__(inject, *args, **kwargs)
