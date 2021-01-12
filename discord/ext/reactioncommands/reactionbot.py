import time
import asyncio
from collections import Counter

import discord
from discord.ext import commands

from .reactionhelp import ReactionHelp
from .reactioncontext import ReactionContext
from .reactioncore import ReactionCommandMixin, ReactionGroupMixin
from .reactionproxy import (ProxyUser, ProxyMember, ProxyTextChannel,
                            ProxyDMChannel, ProxyGuild)

__all__ = ('ReactionBot', 'AutoShardedReactionBot', 'ReactionBotMixin')


class ReactionBotMixin(ReactionGroupMixin):

    def __init__(self, command_prefix, command_emoji, listening_emoji, *args, **kwargs):
        if command_emoji == listening_emoji:
            raise ValueError('command_emoji and listening_emoji cannot be the same')
        self.command_emoji = command_emoji
        self.listening_emoji = listening_emoji
        self.listen_timeout = kwargs.get('listen_timeout', 15)
        self.listen_total_time = kwargs.get('listen_total_time', 120)
        self.active_ctx_sesssions = Counter()
        self.remove_reactions_after = kwargs.get('remove_reactions_after', True)
        self.__debug = kwargs.get('_debug', False)

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

    def _get_message(self, message_id, *, reverse=True):
        messages = self.cached_messages if reverse else reversed(self.cached_messages)
        return discord.utils.get(self.cached_messages, id=message_id) if self._connection._messages else None

    async def _get_x_emoji(self, payload, *, attr):
        emoji = ret = getattr(self, attr)
        if callable(emoji):
            ret = await discord.utils.maybe_coroutine(emoji, self, payload)

        if not isinstance(ret, str):
            try:
                ret = list(ret)
            except TypeError:
                # It's possible that a generator raised this exception.  Don't
                # replace it with our own error if that's the case.
                if isinstance(ret, collections.abc.Iterable):
                    raise

                raise TypeError(f"{attr} must be plain string, iterable of strings, or callable "
                                "returning either of these, not {}".format(ret.__class__.__name__))

            if not ret:
                raise ValueError(f"Iterable {name} must contain at least one prefix")

        return ret

    async def get_command_emoji(self, payload):
        return await self._get_x_emoji(payload, attr='command_emoji')

    async def get_listening_emoji(self, payload):
        if self.listening_emoji is None:
            return None
        return await self._get_x_emoji(payload, attr='listening_emoji')

    async def process_reaction_commands(self, payload):
        context = await self.get_reaction_context(payload)
        await self.reaction_invoke(context)

    async def get_reaction_context(self, payload, *, cls=ReactionContext, check=None):
        command_emoji = await self.get_command_emoji(payload)

        author, channel, guild = self._create_proxies(payload)
        message = channel.get_partial_message(payload.message_id)

        ctx = cls(self, payload, author=author, message=message)
        try:
            # try and exit before emoji stream
            if author == self.user or author.bot:
                return ctx
        except (NameError, AttributeError):
            pass

        maybe_prefix = str(payload.emoji)
        if ((isinstance(command_emoji, str) and maybe_prefix == command_emoji) or
                (isinstance(command_emoji, list) and maybe_prefix in command_emoji)):
            ctx.prefix = maybe_prefix
        else:
            return ctx

        try:
            if not await self.reaction_before_invoke(ctx):
                return ctx
            self.active_ctx_sesssions[ctx.message.id] += 1
            emojis, end_early = await self._wait_for_emoji_stream(ctx, check=check)
            self.active_ctx_sesssions[ctx.message.id] -= 1

            if not end_early:
                ctx.remove_after.append((command_emoji, ctx.author))
            ctx.view = commands.view.StringView(emojis or '')
            ctx.full_emojis = emojis
            invoker = ctx.view.get_word()
            ctx.invoked_with = invoker
            ctx.command = self.get_reaction_command(invoker)
        except Exception as e:
            if self.__debug:
                print(e)
        return ctx

    async def reaction_invoke(self, ctx):
        self.loop.create_task(self.reaction_after_invoke(ctx))
        try:
            await self.invoke(ctx)
        except Exception as e:
            if self.__debug:
                print(e)

    def _create_proxies(self, payload):
        if payload.guild_id:
            guild = self.get_guild(payload.guild_id)
            if not guild:
                # I don't know why I need this
                # who the fuck doesn't have guild intent
                guild = ProxyGuild(self, payload.guild_id)
                author = payload.member
            else:
                author = payload.member or guild.get_member(payload.user_id)

            if not author:
                author = ProxyMember(self, payload.user_id, guild)

            # again, who the fuck doesn't have guild intent
            channel = self.get_channel(payload.channel_id) or ProxyTextChannel(self, payload.channel_id, guild)
        else:
            guild = None
            author = self.get_user(payload.user_id) or ProxyUser(self, payload.user_id)
            # if DMChannel doesn't exist yet
            # could just create it but not sure
            channel = self.get_channel(payload.channel_id) or ProxyDMChannel(self, payload.channel_id, author)

        return author, channel, guild

    async def _wait_for_emoji_stream(self, ctx, *, check=None):
        if not check:
            def check(payload):
                return payload.message_id == ctx.message.id and payload.user_id == ctx.author.id
        command = []
        if self.listen_total_time is not None:
            cutoff = int(time.time()) + self.listen_total_time
        while True:
            tasks = (self.wait_for('raw_reaction_add', check=check),
                     self.wait_for('raw_reaction_remove', check=check))
            done, pending = await asyncio.wait([asyncio.create_task(t) for t in tasks],
                                               timeout=self.listen_timeout,
                                               return_when=asyncio.FIRST_COMPLETED)
            if self.listen_total_time is not None:
                current = int(time.time())
                if current > cutoff:
                    return '', False
            if done:
                #user reacted
                result = done.pop()
                self._cleanup_reaction_tasks(done, pending)
                try:
                    payload = result.result()
                except Exception:
                    return '', False
                emoji = str(payload.emoji)
                if emoji == ctx.prefix:
                    if command:
                        return ''.join(command), True
                    else:
                        return '', True
                elif emoji == ctx.listening_emoji:
                    command.append(' ')
                else:
                    command.append(str(payload.emoji))
            else:
                #user stopped reacting, check if any reactions
                self._cleanup_reaction_tasks(done, pending)
                if command:
                    return ''.join(command), False
                else:
                    return '', False

    def _cleanup_reaction_tasks(self, done, pending):
        # cleanup tasks from emoji waiting
        for future in (done or []):
            future.exception()
        for future in (pending or []):
            future.cancel()

    async def reaction_before_invoke(self, ctx):
        try:
            await self._mc.acquire(ctx)
        except commands.MaxConcurrencyReached:
            return False
        #add support for callable here
        listening_emoji = await self.get_listening_emoji(ctx.payload)
        ctx.listening_emoji = listening_emoji
        if listening_emoji is not None:
            try:
                await ctx.message.add_reaction(listening_emoji)
                ctx.remove_after.append((listening_emoji, ctx.me))
            except Exception:
                pass
        return True

    async def reaction_after_invoke(self, ctx):
        await self._mc.release(ctx)
        if self.remove_reactions_after:
            try:
                can_remove = ctx.channel.permissions_for(ctx.me).manage_messages
            except:
                can_remove = True
            for emoji, user in ctx.remove_after:
                if user == self.user:
                    if not (emoji == ctx.listening_emoji and self.active_ctx_sesssions[ctx.message.id]):
                        try:
                            await ctx.message.remove_reaction(emoji, self.user)
                        except Exception:
                            pass
                elif can_remove:
                    try:
                        await ctx.message.remove_reaction(emoji, user)
                    except Exception:
                        pass
            if not self.active_ctx_sesssions[ctx.message.id]:
                try:
                    del self.active_ctx_sesssions[ctx.message.id]
                except KeyError:
                    pass


class ReactionBot(ReactionBotMixin, commands.Bot):
    pass


class AutoShardedReactionBot(ReactionBotMixin, commands.AutoShardedBot):
    pass
