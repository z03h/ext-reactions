import asyncio

import discord
from discord.ext import commands

from .reactionhelp import ReactionHelp
from .reactioncontext import ReactionContext
from .reactioncore import ReactionCommandMixin, ReactionGroupMixin


class ReactionBotBase(ReactionGroupMixin):
    def __init__(self, command_prefix, command_emoji, listening_emoji, *args, **kwargs):
        if not command_emoji:
            raise ValueError('command_emoji must be a str')
        if not listening_emoji:
            raise ValueError('listening_emoji must be a str')
        self.command_emoji = command_emoji
        self.listening_emoji = listening_emoji
        self.listen_timeout = kwargs.get('timeout', 15)
        kwargs.setdefault('help_command', ReactionHelp())
        super().__init__(command_prefix=command_prefix, *args, **kwargs)
        self._mc = commands.MaxConcurrency(1, per=commands.BucketType.user, wait=False)

    async def get_context(self, *args, **kwargs):
        ctx = await super().get_context(*args, **kwargs)
        try:
            ctx.reaction_command = False
        except AttributeError:
            pass
        return ctx

    async def on_raw_reaction_add(self, payload):
        await self.process_reaction_commands(payload)

    async def process_reaction_commands(self, payload):
        #make a pseudo context
        context = await self.get_reaction_context(payload)
        await self.reaction_invoke(context)

    async def get_reaction_context(self, payload, *, cls=ReactionContext):
        #add support for callable here
        command_emoji = self.command_emoji

        g_id = payload.guild_id
        u_id = payload.user_id
        guild = self.get_guild(g_id)
        user = guild.get_member(u_id) if guild else self.get_user(u_id)

        if not user:
            user = discord.Object(id=u_id)

        channel = self.get_channel(payload.channel_id) or discord.Object(id=payload.channel_id)

        ctx = cls(self, payload, user, channel)

        if str(payload.emoji) != command_emoji:
            return ctx
        ctx.prefix = command_emoji

        try:
            emojis, end_early = await self.wait_emoji_stream(ctx)
            if not end_early:
                ctx.remove_after.append((command_emoji, user))
            ctx.view = commands.view.StringView(emojis or '')
            ctx.full_emojis = emojis
            invoker = ctx.view.get_word()
            ctx.invoked_with = invoker
            ctx.command = self.get_reaction_command(invoker)
        except Exception as e:
            print(e)
        return ctx

    async def reaction_invoke(self, context):
        try:
            await self.invoke(context)
        except Exception as e:
            print(e)
        finally:
            await self.reaction_after_invoke(context)

    def _cleanup_tasks(self, done, pending):
        # cleanup tasks from emoji waiting
        for future in (done or []):
            future.exception()
        for future in (pending or []):
            future.cancel()

    async def wait_emoji_stream(self, context, *, check=None):
        if not await self.reaction_before_invoke(context):
            return '', False
        if not check:
            def check(payload):
                return payload.message_id == context.message.id and payload.user_id == context.author.id
        command = []
        while True:
            tasks = (self.wait_for('raw_reaction_add', check=check),
                     self.wait_for('raw_reaction_remove', check=check))
            done, pending = await asyncio.wait([asyncio.create_task(t) for t in tasks],
                                               timeout=self.listen_timeout,
                                               return_when=asyncio.FIRST_COMPLETED)
            if done:
                #user reacted
                result = done.pop()
                self._cleanup_tasks(done, pending)
                try:
                    payload = result.result()
                except Exception:
                    return '', False
                emoji = str(payload.emoji)
                if emoji == self.command_emoji:
                    if command:
                        return ''.join(command), True
                    else:
                        return '', True
                elif emoji == context.listening_emoji:
                    command.append(' ')
                else:
                    command.append(str(payload.emoji))
            else:
                #user stopped reacting, check if any reactions
                self._cleanup_tasks(done, pending)
                if command:
                    return ''.join(command), False
                else:
                    return '', False

    async def reaction_before_invoke(self, context):
        try:
            await self._mc.acquire(context)
        except commands.MaxConcurrencyReached:
            return False
        #add support for callable here
        listening_emoji = self.listening_emoji
        context.listening_emoji = listening_emoji
        try:
            await context.message.add_reaction(listening_emoji)
            context.remove_after.append((listening_emoji, context.me))
        except Exception:
            pass
        return True

    async def reaction_after_invoke(self, context):
        await self._mc.release(context)
        can_remove = context.channel.permissions_for(context.me).manage_messages
        for emoji, user in context.remove_after:
            if user == self.user or can_remove:
                try:
                    await context.message.remove_reaction(emoji, user)
                except Exception:
                    pass

class ReactionBot(ReactionBotBase, commands.Bot):
    pass

class AutoShardedReactionBot(ReactionBotBase, commands.AutoShardedBot):
    pass
