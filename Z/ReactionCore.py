import re
import asyncio

import discord
from discord.ext import commands

from .ReactionHelp import ReactionHelp
from .ReactionContext import ReactionContext
from .ReactionCommand import ReactionCommandMixin

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


class ReactionBotBase(commands.Bot):
    def __init__(self, command_prefix, command_emoji, listening_emoji, *args, **kwargs):
        if not command_emoji:
            raise ValueError('command_emoji must be a str')
        if not listening_emoji:
            raise ValueError('listening_emoji must be a str')
        self.command_emoji = command_emoji
        self.listening_emoji = listening_emoji
        kwargs.setdefault('help_command', ReactionHelp())
        self.emoji_mapping = _EmojiInsensitiveDict() if kwargs.get('case_insensitive') else {}
        super().__init__(command_prefix=command_prefix, *args, **kwargs)
        self.listen_timeout = kwargs.get('timeout', 10)
        self._mc = commands.MaxConcurrency(1, per=commands.BucketType.user, wait=False)

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

    def get_emoji_command(self, query):
        return self.emoji_mapping.get(query)

    async def get_context(self, *args, **kwargs):
        ctx = await super().get_context(*args, **kwargs)
        try:
            ctx.reaction_command = False
        except AttributeError:
            pass
        return ctx

    async def on_raw_reaction_add(self, payload):
        await self.process_reaction_commands(payload)

    def get_reaction_context(self, payload, *, cls=ReactionContext):
        g_id = payload.guild_id
        u_id = payload.user_id
        if guild:=self.get_guild(g_id):
            user = guild.get_member(u_id)
        else:
            user = self.get_user(u_id)
        if user and user.bot:
            return
        if not user:
            user = discord.Object(id=u_id)
        channel = self.get_channel(payload.channel_id) or discord.Object(id=payload.channel_id)
        return cls(self, payload, user, channel)

    async def process_reaction_commands(self, payload):
        if str(payload.emoji) != self.command_emoji:
            return
        #make a pseudo context
        context = self.get_reaction_context(payload)
        if await self.reaction_before_invoke(context):
            try:
                emoji = await self.wait_emoji_stream(payload.user_id, payload.message_id)
                if emoji:
                    command = self.get_emoji_command(emoji)
                    if command:
                        context.set_command(self.command_emoji, command, emoji)
                        await self.invoke(context)
            except Exception as e:
                pass
            finally:
                await self.reaction_after_invoke(context)

    def _cleanup_tasks(self, done, pending):
        # cleanup tasks from emoji waiting
        for future in (done or []):
            future.exception()
        for future in (pending or []):
            future.cancel()

    async def wait_emoji_stream(self, user_id, msg_id, *, check=None):
        if not check:
            def check(payload):
                return payload.message_id == msg_id and payload.user_id == user_id
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
                    return None
                emoji = str(payload.emoji)
                if emoji == self.command_emoji:
                    if command:
                        return ''.join(command)
                    else:
                        return None
                command.append(str(payload.emoji))
            else:
                #user stopped reacting, check if any reactions
                self._cleanup_tasks(done, pending)
                if command:
                    return ''.join(command)
                else:
                    return None

    async def reaction_before_invoke(self, context):
        try:
            await self._mc.acquire(context)
        except commands.MaxConcurrencyReached:
            return False
        try:
            await self.http.add_reaction(context.channel.id, context.message.id, self.listening_emoji)
        except Exception:
            pass
        return True

    async def reaction_after_invoke(self, context):
        await self._mc.release(context)
        if context.channel.permissions_for(context.me).manage_messages:
            try:
                await context.message.clear_reactions()
            except discord.NotFound:
                pass
            except Exception:
                try:
                    await self.http.remove_own_reaction(context.channel.id, context.message.id, self.listening_emoji)
                except Exception:
                    pass
        else:
            try:
                await self.http.remove_own_reaction(context.channel.id, context.message.id, self.listening_emoji)
            except Exception:
                pass

    def reaction_command(self, emojis, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = reaction_command(emojis, *args, **kwargs)(func)
            self.add_command(result)
            return result
        return decorator


class ReactionCommand(ReactionCommandMixin, commands.Command):
    pass

def reaction_command(emojis, name=None, cls=None, **attrs):
    if cls is None:
        cls = ReactionCommand

    def decorator(func):
        if isinstance(func, commands.Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, emojis=emojis, **attrs)

    return decorator
