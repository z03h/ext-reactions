import discord
from discord.ext import commands

from .utils import scrub_emojis
from .reactionerrors import ReactionOnlyCommand

__all__ = ('ReactionCommand',
           'ReactionGroup',
           'reaction_command',
           'reaction_group',
           'ReactionCommandMixin',
           'ReactionGroupMixin')


class _EmojiInsensitiveDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _clean(self, k):
        return scrub_emojis(k)

    def __contains__(self, k):
        return super().__contains__(self._clean(k))

    def __delitem__(self, k):
        return super().__delitem__(self._clean(k))

    def __getitem__(self, k):
        return super().__getitem__(self._clean(k))

    def get(self, k, default=None):
        return super().get(self._clean(k), default)

    def pop(self, k, default=None):
        return super().pop(self._clean(k), default)

    def __setitem__(self, k, v):
        super().__setitem__(self._clean(k), v)


class ReactionCommandMixin:
    """Mixin for ReactinCommands

    Implements ReactionCommand functionality for :class:`ReactionCommand`
    and :class:`ReactionGroup`.

    Parameters
    ----------
    emojis: Union[:class:`str`, list]
        emoji or list of emojis that the command cane be invoked with
    invoke_with_message: :class:`bool`
        Whether the command can be invoked from a message. Defaults to ``True``.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        emojis = kwargs.get('emojis')
        if not emojis:
            raise ValueError(f'emojis cannot be empty for command {self.name}')
        self.invoke_with_message = kwargs.get('invoke_with_message', True)
        self.emojis = [emojis] if isinstance(emojis, str) else list(emojis)

    async def can_run(self, ctx):
        """Overwritten to also raise
        :exc:`.ReactionOnlyCommand` for commands that have
        :attr:`invoke_with_message <.ReactionCommand.invoke_with_message>`
        set to ``False``.

        Otherwise the same as :meth:`can_run() <discord.ext.commands.Command.can_run>`.

        Parameters
        ----------
        ctx: :class:`Context <discord.ext.reactioncommands.ReactionContext>`
            Context to check if it can run against.

        Raises
        ------
        :class:`discord.ext.commands.CommandError`
            Error for why command can't be run

        Returns
        -------
        :class:`bool`
            Whether or not the command can run.
        """
        if not self.enabled:
            raise commands.DisabledCommand('{0.name} command is disabled'.format(self))
        if not getattr(ctx, 'reaction_command', False) and not self.invoke_with_message:
            raise ReactionOnlyCommand('{0.name} command is only usable with reactions'.format(self))
        return await super().can_run(ctx)

    async def _parse_arguments(self, ctx):
        """
        .. Warning::
            Argument converting had to change a lot for reaction
            commands.

            No way to get input so there is **no conversion** or parsing done here
            unless it was invoked from a message.

            When :class:`.ReactionCommand` or :class:`.ReactionGroup` is invoked from
            a reaction, args will be filled with their default value or ``None``.
        """
        is_reaction = getattr(ctx, 'reaction_command', False)

        if is_reaction:
            ctx.args = [ctx] if self.cog is None else [self.cog, ctx]
            ctx.kwargs = {}
            args = ctx.args
            kwargs = ctx.kwargs
            iterator = iter(self.params.items())

            if self.cog is not None:
                # we have 'self' as the first parameter so just advance
                # the iterator and resume parsing
                try:
                    next(iterator)
                except StopIteration:
                    fmt = 'Callback for {0.name} command is missing "self" parameter.'
                    raise discord.ClientException(fmt.format(self))

            # next we have the 'ctx' as the next parameter
            try:
                next(iterator)
            except StopIteration:
                fmt = 'Callback for {0.name} command is missing "ctx" parameter.'
                raise discord.ClientException(fmt.format(self))

            for name, param in iterator:
                arg = None if param.default is param.empty else param.default
                if param.kind == param.KEYWORD_ONLY:
                    kwargs[name] = arg
                else:
                    args.append(arg)
        else:
            await super()._parse_arguments(ctx)


class ReactionGroupMixin:
    """Mixin for ReactionGroups.

    Implements reaction group functionality for :class:`.ReactionBot` and
    :class:`.ReactionGroup`.

    Parameters
    ----------
    case_insensitive: Optional[:class:`bool`]
        In addition to making normal commands case insensitive, attempts to
        normalize emojis by removing different skin colored and gendered
        modifiers when being invoked.

        Ex: 👍🏿/👍🏾/👍🏽/👍🏼/👍🏻 --> 👍 or 🧙‍♂️/🧙‍♀️ --> 🧙
    """

    def __init__(self, *args, **kwargs):
        self.emoji_mapping = _EmojiInsensitiveDict() if kwargs.get('case_insensitive') else {}
        super().__init__(*args, **kwargs)

    @property
    def reaction_commands(self):
        """set[:class:`.ReactionCommand`]: Unique registered reaction commands.
        """
        return set(self.emoji_mapping.values())

    def add_command(self, command):
        """Adds a command to the internal list.

        If the command passed has attribute ``emojis``, will be treated as
        an instance of :class:`.ReactionCommand`.

        Adds :attr:`.ReactionCommand.emojis` to the internal mapping of
        reaction commands.

        Parameters
        ----------
        command: :class:`commands.Command <discord.ext.commands.Command>`
            The command to add
        """
        try:
            if any(emoji in self.emoji_mapping for emoji in command.emojis):
                raise commands.CommandRegistrationError(' '.join(command.emojis))
            try:
                super().add_command(command)
            except Exception as e:
                raise e
            else:
                for emoji in command.emojis:
                    self.emoji_mapping[emoji] = command
        except AttributeError as e:
            super().add_command(command)

    def remove_command(self, name):
        """Remove a command to the internal list by name.

        Attempts to remove :attr:`emojis <.ReactionCommand.emojis>` from the
        internal mapping of ``emoji: Command``. Be wary of manually updating
        :attr:`emojis <.ReactionCommand.emojis>`.

        Parameters
        ----------
        name: :class:`str`
            Name of the command to remove

        Returns
        -------
        Optional[:class:`commands.Command <discord.ext.commands.Command>`]
            The command that was removed
        """
        command = self.all_commands.pop(name, None)

        # does not exist
        if command is None:
            return None

        if name in command.aliases:
            # we're removing an alias so we don't want to remove the rest
            return command
        # only remove emojis if we fully remove the command
        try:
            if name and command:
                for emoji in command.emojis:
                    self.emoji_mapping.pop(emoji, None)
        except AttributeError:
            pass
        # we're not removing the alias so let's delete the rest of them.
        for alias in command.aliases:
            cmd = self.all_commands.pop(alias, None)
            # in the case of a CommandRegistrationError, an alias might conflict
            # with an already existing command. If this is the case, we want to
            # make sure the pre-existing command is not removed.
            if cmd not in (None, command):
                self.all_commands[alias] = cmd
        return command

    def remove_reaction_command(self, emoji):
        """Attempts to remove a reaction command by emoji

        Parameters
        ----------
        emoji: :class:`str`
            emoji of the reaction command to remove

        Returns
        -------
        Optional[:class:`.ReactionCommand`]
            The command that was removed or ``None``
        """
        command = self.get_reaction_command(emoji)
        if command:
            return self.remove_command(command.name)
        return None

    def get_reaction_command(self, name):
        """Gets a command by emoji.

        Parameters
        ----------
        name: :class:`str`
            Emoji(s) for the command.

        Returns
        -------
        Optional[:class:`.ReactionCommand`]
            The command or ``None``
        """
        if ' ' not in name:
            return self.emoji_mapping.get(name)
        names = name.split(' ')
        if not names:
            return None
        obj = self.emoji_mapping.get(names[0])
        if not isinstance(obj, ReactionGroupMixin):
            return obj
        for name in names[1:]:
            try:
                obj = obj.emoji_mapping[name]
            except (AttributeError, KeyError):
                return None
        return obj

    def reaction_command(self, emojis, *args, **kwargs):
        """Decorator that creates and adds a command to the internal list of
        commands. Calls :func:`@reaction_command() <.reaction_command>`.

        ``args`` and ``kwargs`` should be the same as normal :meth:`@Group.command() <discord.ext.commands.Group.command>`.

        Parameters
        ----------
        emojis: Union[:class:`list`, :class:`str`]
            An emoji or list of emojis that can be used to invoke this command.
        invoke_with_message: Optional[:class:`bool`]
            Whether the command can be invoke with messages. Default value is ``True``.

        Returns
        -------
        :class:`Callable`
            A decorator that converts the provided method into a Command, adds it to the
            internal lsit of commands, then returns it.
        """
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = reaction_command(emojis, *args, **kwargs)(func)
            self.add_command(result)
            return result
        return decorator

    def reaction_group(self, emojis, *args, **kwargs):
        """Shortcut decorator that creates and adds a group to the internal list
        of commands. Calls :func:`@reaction_group() <.reaction_group>`.

        ``args`` and ``kwargs`` should be the same as normal :meth:`@Group.group() <discord.ext.commands.Group.group>`.

        Parameters
        ----------
        emojis: Union[:class:`list`, :class:`str`]
            An emoji or list of emojis that can be used to invoke this group.
        invoke_with_message: Optional[:class:`bool`]
            Whether the command can be invoke with messages. Default value is ``True``.

        Returns
        -------
        :class:`Callable`
            A decorator that converts the provided method into a Group, adds it to the
            list of commands, then returns it.
        """
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = reaction_group(emojis, *args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

class ReactionCommand(ReactionCommandMixin, commands.Command):
    """Basically the same as :class:`commands.Command <discord.ext.commands.Command>`
    but with modified argument conversion flow to allow reaction invoke. Can be
    invoked with messages or reactions by default.

    Other ``args`` and ``kwargs`` should be the same as
    :class:`commands.Command <discord.ext.commands.Command>`.

    Attributes
    ----------
    emojis: :class:`list`
        A list of emojis that the command can be invoked with. This attribute
        will always be a list even if the input is a single emoji.
    invoke_with_message: Optional[:class:`bool`]
        Whether the command can be invoked with messages or not. Pass ``False``
        to only allow reaction invoke. Default value is ``True``.
    """
    pass


class ReactionGroup(ReactionGroupMixin, ReactionCommandMixin, commands.Group):
    """Basically the same as :class:`commands.Group <discord.ext.commands.Group>`
    but with modified argument conversion flow to allow reaction invoke. Can be
    invoked with messages or reactions by default.

    Other ``args`` and ``kwargs`` should be the same as
    :class:`commands.Group <discord.ext.commands.Group>`.

    Attributes
    ----------
    emojis: :class:`list`
        A list of emojis that the command can be invoked with. This attribute
        will always be a list even if the input is a single emoji.
    invoke_with_message: Optional[:class:`bool`]
        Whether the command can be invoked with messages or not. Pass ``False``
        to only allow reaction invoke. Default value is ``True``.
    case_insensitive: Optional[:class:`bool`]
        In addition to making normal commands case insensitive, attempts to
        normalize emojis by removing different skin colored and gendered
        modifiers when being invoked.

        Ex: 👍🏿/👍🏾/👍🏽/👍🏼/👍🏻 --> 👍 or 🧙‍♂️/🧙‍♀️ --> 🧙
    """
    async def invoke(self, ctx):
        is_reaction = getattr(ctx, 'reaction_command', False)

        if is_reaction:
            ctx.invoked_subcommand = None
            ctx.subcommand_passed = None
            early_invoke = not self.invoke_without_command
            if early_invoke:
                await self.prepare(ctx)

            view = ctx.view
            previous = view.index
            view.skip_ws()
            trigger = view.get_word()

            if trigger:
                ctx.subcommand_passed = trigger
                ctx.invoked_subcommand = self.get_reaction_command(trigger)

            if early_invoke:
                injected = commands.core.hooked_wrapped_callback(self, ctx, self.callback)
                await injected(*ctx.args, **ctx.kwargs)

            if trigger and ctx.invoked_subcommand:
                ctx.invoked_with = trigger
                await ctx.invoked_subcommand.invoke(ctx)
            elif not early_invoke:
                # undo the trigger parsing
                view.index = previous
                view.previous = previous
                await super().invoke(ctx)
        else:
            await super().invoke(ctx)

def reaction_command(emojis, name=None, cls=None, **attrs):
    """Decorator that creates a command. Default class is :class:`.ReactionCommand`.

    ``**attrs`` should be the same as
    :func:`@commands.command() <discord.ext.commands.command>`.

    Parameters
    ----------
    emojis: Union[:class:`list`, :class:`str`]
        An emoji or list of emojis that can be used to invoke this command.
    invoke_with_message: Optional[:class:`bool`]
        Whether the command can be invoked from messages. Default value is ``True``.

    Returns
    -------
    :class:`Callable`
        A decorator that converts the provided method into a Command, then returns it
    """
    if cls is None:
        cls = ReactionCommand

    def decorator(func):
        if isinstance(func, commands.Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, emojis=emojis, **attrs)

    return decorator

def reaction_group(emojis, name=None, **attrs):
    """Decorator that creates a group. Sets the ``cls`` kwarg to
    :class:`.ReactionGroup`.

    ``**attrs`` should be the same as
    :func:`@commands.group() <discord.ext.commands.group>`.

    Parameters
    ----------
    emojis: Union[:class:`list`, :class:`str`]
        An emoji or list of emojis that can be used to invoke this command.
    invoke_with_message: Optional[:class:`bool`]
        Whether the command can be invoked from messages. Default value is ``True``.
    case_insensitive: Optional[:class:`bool`]
        In addition to making normal commands case insensitive, attempts to
        normalize emojis by removing different skin colored and gendered
        modifiers when being invoked.

        Ex: 👍🏿/👍🏾/👍🏽/👍🏼/👍🏻 --> 👍 or 🧙‍♂️/🧙‍♀️ --> 🧙

    Returns
    -------
    :class:`Callable`
        A decorator that converts the provided method into a Group, then returns it
    """
    attrs.setdefault('cls', ReactionGroup)
    return reaction_command(emojis, name=name, **attrs)
