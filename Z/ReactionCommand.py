import discord


class ReactionCommandMixin:
    """docstring for ClassName"""
    def __init__(self, *args, **kwargs):
        emojis = kwargs.get('emojis')
        if not emojis:
            raise ValueError(f'Emojis cannot be empty for {self.name}')
        self.emojis = [emojis] if isinstance(emojis, str) else emojis
        super().__init__(*args, **kwargs)

    async def _parse_arguments(self, ctx):
        if ctx.reaction_command:
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
                if param.kind == param.KEYWORD_ONLY:
                    kwargs[name] = None
                else:
                    args.append(None)
        else:
            await super()._parse_arguments(ctx)
