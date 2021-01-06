import asyncio

import discord
from discord.ext import commands

from .Context import ReactionContext
from .ReactionCommand import reaction_command
from .ReactionHelp import ReactionHelp

class ReactionBotBase(commands.Bot):
    def __init__(self, command_emoji, listening_emoji, *args, **kwargs):
        kwargs.setdefault('help_command', ReactionHelp())
        self.emoji_mapping = {}
        super().__init__(command_prefix='', *args, **kwargs)
        self.command_prefix = ''
        self.command_emoji = command_emoji
        self.listening_emoji = listening_emoji
        self.listen_timeout = kwargs.get('timeout', 10)
        self._mc = commands.MaxConcurrency(1, per=commands.BucketType.user, wait=False)

    async def on_message(self, message):
        pass

    def add_command(self, command):
        if any(emoji in self.emoji_mapping for emoji in command.emojis):
            raise CommandRegistrationError(emoji)
        for emoji in command.emojis:
            self.emoji_mapping[emoji] = command
        try:
            super().add_command(command)
        except Exception as e:
            for emoji in command.emojis:
                self.emoji_mapping.pop(emoji)
            raise e

    def remove_command(self, command):
        cmd = super().remove_command(command)
        if cmd:
            for emoji in cmd.emojis:
                self.emoji_mapping.pop(emoji, None)
        return cmd

    def get_emoji_command(self, query):
        return self.emoji_mapping.get(query)

    async def on_raw_reaction_add(self, payload):
        await self.process_reaction_commands(payload)

    async def process_reaction_commands(self, payload):
        if str(payload.emoji) != self.command_emoji:
            return
        g_id = payload.guild_id
        u_id = payload.user_id
        if guild:=self.get_guild(g_id):
            user = guild.get_member(u_id)
        else:
            user = self.get_user(u_id)
        if not user or user.bot:
            return
        channel = self.get_channel(payload.channel_id) or discord.Object(id=payload.channel_id)
        #make a pseudo context
        context = ReactionContext(self, payload.message_id, user, channel, guild)
        if await self.r_before_invoke(context):
            emoji = await self.wait_emoji_stream(u_id, payload.message_id)
            if not emoji:
                return
            command = self.get_emoji_command(emoji)
            if command:
                context.set_command(command, emoji)
                await self.invoke(context)
            else:
                command = self.get_command('help')
                context.set_command(command, self.command_emoji)
                await self.invoke(context)
            await self.r_after_invoke(context)

    def _cleanup_tasks(self, done, pending):
        # cleanup tasks from emoji waiting
        for future in (done or []):
            future.exception()
        for future in (pending or []):
            future.cancel()

    async def wait_emoji_stream(self, user_id, msg_id):
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

    async def r_before_invoke(self, context):
        try:
            await self._mc.acquire(context)
        except commands.MaxConcurrencyReached:
            return False
        if self.listening_emoji:
            try:
                await self.http.add_reaction(context.channel.id, context.message.id, self.listening_emoji)
            except discord.HTTPException:
                pass
        return True

    async def r_after_invoke(self, context):
        await self._mc.release(context)
        if self.listening_emoji:
            await self.http.remove_own_reaction(context.channel.id, context.message.id, self.listening_emoji)


    def command(self, emojis, *args, **kwargs):
        def decorator(func):
            kwargs.setdefault('parent', self)
            result = reaction_command(emojis, *args, **kwargs)(func)
            self.add_command(result)
            return result
        return decorator

