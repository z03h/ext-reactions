import re

import discord
from discord.ext import commands


class _EmojiInsensitiveDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #skin colors, genders
        to_remove = '\U0001f3fb|\U0001f3fc|\U0001f3fd|\U0001f3fe|\U0001f3ff|' \
                    '\u200d[\u2642\u2640]\ufe0f'
        self.clean = re.compile(to_remove)

    def _clean(self, k):
        return self.clean.sub('', k)

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        emojis = kwargs.get('emojis')
        if not emojis:
            raise ValueError(f'emojis cannot be empty for {self.name}')
        self.invoke_with_message = kwargs.get('invoke_with_message', True)
        self.emojis = [emojis] if isinstance(emojis, str) else emojis

    async def _parse_arguments(self, ctx):
        try:
            is_reaction = ctx.reaction_command
        except AttributeError:
            is_reaction = False

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
    def __init__(self, *args, **kwargs):
        self.emoji_mapping = _EmojiInsensitiveDict() if kwargs.get('case_insensitive') else {}
        super().__init__(*args, **kwargs)

    def add_command(self, command):
        try:
            if any(emoji in self.emoji_mapping for emoji in command.emojis):
                raise commands.CommandRegistrationError(' '.join(command.emojis))
            for emoji in command.emojis:
                self.emoji_mapping[emoji] = command
            try:
                super().add_command(command)
            except Exception as e:
                for emoji in command.emojis:
                    self.emoji_mapping.pop(emoji, None)
                raise e
        except AttributeError as e:
            super().add_command(command)

    def remove_command(self, command):
        cmd = super().remove_command(command)
        try:
            if cmd:
                for emoji in cmd.emojis:
                    self.emoji_mapping.pop(emoji, None)
        except AttributeError:
            pass
        return cmd

    def get_reaction_command(self, name):
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
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = reaction_command(emojis, *args, **kwargs)(func)
            self.add_command(result)
            return result
        return decorator

    def reaction_group(self, emojis, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = reaction_group(emojis, *args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

class ReactionCommand(ReactionCommandMixin, commands.Command):
    pass


class ReactionGroup(ReactionGroupMixin, ReactionCommandMixin, commands.Group):
    def __init__(self, *args, **kwargs):
        self.invoke_without_command = kwargs.get('invoke_without_command', False)
        super().__init__(*args, **kwargs)

    async def invoke(self, ctx):
        try:
            reaction_command = ctx.reaction_command
        except AttributeError:
            reaction_command = False
        if reaction_command:
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
    if cls is None:
        cls = ReactionCommand

    def decorator(func):
        if isinstance(func, commands.Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, emojis=emojis, **attrs)

    return decorator

def reaction_group(emojis, name=None, cls=None, **attrs):
    attrs.setdefault('cls', ReactionGroup)
    return reaction_command(emojis, name=name, **attrs)
