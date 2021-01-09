import discord


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
