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
    """Mixin for implementing reaction commands to Bot"""
    def __init__(self, command_prefix, command_emoji, listening_emoji, *args,
                 listen_timeout=15, listen_total_timeout=120, remove_reactions_after=True,
                 **kwargs):
        self.command_emoji = command_emoji
        self.listening_emoji = listening_emoji
        self.listen_timeout = listen_timeout
        self.listen_total_timeout = listen_total_timeout
        self.active_ctx_sesssions = Counter()
        self.remove_reactions_after = remove_reactions_after
        self.__debug = kwargs.get('_debug', False)

        kwargs.setdefault('help_command', ReactionHelp())
        super().__init__(command_prefix=command_prefix, *args, **kwargs)
        self._mc = commands.MaxConcurrency(1, per=commands.BucketType.user, wait=False)

    async def get_context(self, message, *, cls=commands.Context):
        """Functions exactly the same as original :meth:`discord.ext.commands.Bot.get_context`.

        Only difference is this function will attempt to set attribute
        `ctx.reaction_command`` to ``False`` to indicate it is a message command.

        Returns
        -------
        :class:`Context <discord.ext.commands.Context>`
            The context from message
        """
        ctx = await super().get_context(message, cls=cls)
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

    async def _get_x_emoji(self, payload, *, attr, str_only=False):
        emoji = ret = getattr(self, attr)
        if callable(emoji):
            ret = await discord.utils.maybe_coroutine(emoji, self, payload)

        if not isinstance(ret, str):
            if str_only:
                raise TypeError(f"{attr} must be plain string or None"
                                "returning either of these, not {}".format(ret.__class__.__name__))
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
        """Method that gets the :attr:`.ReactionBot.command_emoji` or list of
        emojis that can be used to start listening for commands.

        Reaction mirror to :meth:`discord.ext.commands.Bot.get_prefix`.

        Parameters
        ----------
        payload: :class:`discord.RawReactionActionEvent`
            payload to start getting context from

        Returns
        -------
        Union[:class:`list`, :class:`str`]
            A list of emojis or a single emoji that the bot is
            listening for.
        """
        return await self._get_x_emoji(payload, attr='command_emoji')

    async def get_listening_emoji(self, payload):
        """Method that gets the listening_emoji that is used for group invoke
        and letting the user know the bot is listening.

        Parameters
        ----------
        payload: :class:`discord.RawReactionActionEvent`
            payload to start getting context from

        Returns
        -------
        Optional[:class:`str`]
            A single emoji or ``None``. If not ``None`` the bot will add as a
            reaction to indicate it is listening for reactions.
        """
        if self.listening_emoji is None:
            return None
        return await self._get_x_emoji(payload, attr='listening_emoji', str_only=True)

    async def reaction_invoke(self, ctx):
        """Invokes a context

        Parameters
        ----------
        ctx: :class:`.reactioncommands.ReactionContext`
            context to invoke
        """
        await self.reaction_after_processing(ctx)
        try:
            await self.invoke(ctx)
        except Exception as e:
            if self.__debug:
                print(e)


    async def get_reaction_context(self, payload, *, cls=ReactionContext, check=None):
        """Creates a :class:`.reactioncommands.ReactionContext` from payload.

        A lot of weird sh*t happens here. If something is not cached, a proxy
        object where only ``id`` is set is used instead. It may have attributes
        set to other proxy objects. These proxy objects `should` behave similar
        to :class:`discord.PartialMessage`, but subclassed from their originals.
        Not every method will work so good luck :)

        Reaction mirror to :meth:`discord.ext.commands.Bot.get_context`.

        Parameters
        ----------
        payload: :class:`discord.RawReactionActionEvent`
            payload to start getting context from
        cls:
            The class that will be used for the context.
        check: Optional[Callable[:class:`discord.RawReactionActionEvent`]]
            Check that will be passed to ``wait_for``. Default check will
            return ``True`` for payload where ``payload.message_id == ctx.message.id
            and payload.user_id == ctx.author.id``.

        Returns
        -------
        :class:`.reactioncommands.ReactionContext`
            The context to invoke.
        """
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
            if not await self.reaction_before_processing(ctx):
                return ctx
            self.active_ctx_sesssions[ctx.message.id] += 1
            try:
                emojis, end_early = await asyncio.wait_for(self._wait_for_emoji_stream(ctx, check=check),
                                                           timeout=self.listen_total_timeout)
            except asyncio.TimeoutError:
                emojis = ''
                end_early = False

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

    async def process_reaction_commands(self, payload):
        """Gets context and invokes from a payload. Takes :class:`payload <discord.RawReactionActionEvent>`
        from :func:`raw_reaction_add <discord.on_raw_reaction_add>` or
        :func:`raw_reaction_remove <discord.on_raw_reaction_remove>`.

        Reaction mirror to :meth:`discord.ext.commands.Bot.process_commands`.

        .. note::
            If you overwrite :func:`raw_reaction_add <discord.on_raw_reaction_add>`
            or :meth:`discord.ext.commands.Bot.event`,
            don't forget to add this so reaction commands will still work.

        Parameters
        ----------
        payload: :class:`discord.RawReactionActionEvent`
            Payload to get context and invoke from.
        """
        context = await self.get_reaction_context(payload)
        await self.reaction_invoke(context)

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

        while True:
            tasks = (self.wait_for('raw_reaction_add', check=check),
                     self.wait_for('raw_reaction_remove', check=check))
            done, pending = await asyncio.wait([asyncio.create_task(t) for t in tasks],
                                               timeout=self.listen_timeout,
                                               return_when=asyncio.FIRST_COMPLETED)
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

    async def reaction_before_processing(self, ctx):
        """Method that is called after verifying the command emoji and before
        the command input is added by the user. Determines if the bot should
        listen to reactions. :attr:`.ReactionBot.listening_emoji` is added here.

        .. note::
            This method prevents users from starting multiple listening sessions
            and has some cleanup that is done in :meth:`.reaction_after_processing`.
            If you overwrite one you should probably overwrite the other or call
            ``super()``.

        Parameters
        ----------
        ctx: :class:`.reactioncommands.ReactionContext`
            Context that may be invoked.

        Returns
        -------
         :class:`bool`
            Whether the bot should continue listening for reactions or not.
        """
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

    async def reaction_after_processing(self, ctx):
        """Method that is called after verifying the command and before checks,
        ``@before_invoke``, and command invoke. If :attr:`.ReactionBot.remove_reactions_after`
        is ``True``, they will be removed here.

        .. note::
            This method cleans up after :meth:`.reaction_before_processing`.
            If you overwrite one you should probably overwrite the other or call
            ``super()``.

        Parameters
        ----------
        ctx: :class:`.reactioncommands.ReactionContext`
            Context that will be invoked.
        """
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
    """Discord Bot subclass that adds reaction commands.
    Subclass of :class:`discord.ext.commands.Bot`.

    All other ``args`` and ``kwargs`` should be the same as :class:`discord.ext.commands.Bot`.

    Attributes
    ----------
        command_emoji: Union[:class:`Callable`, :class:`list`, :class:`str`]
            Similar to command_prefix, but for starting emoji commands.
            Can be a string, list of strings, or callable/coroutine with the bot as its
            first parameter and :class:`discord.RawReactionActionEvent` as its
            second parameter. This callable should return a string or list of strings.
        listening_emoji: Union[:class:`Callable`, :class:`str`, :class:`None`]
            Same as command_emoji. Can be ``None`` if you don't want to invoke
            emoji groups with reactions or add a reaction on every
            :attr:`command_emoji` reaction.
        listen_timeout: Optional[:class:`int`]
            Time in seconds that the bot will listen for emojis from a user.
            Will reset after each emoji added or removed. Pass ``None`` to disable.
            Default value is ``15``.
        listen_total_timeout: Optional[:class:`int`]
            Total time in seconds the bot will listen to a user. Prevents the user
            from adding or removing emojis and keeping the listen session active
            forever. Pass ``None`` to disable.
            Default value is ``120``.
        remove_reactions_after: Optional[:class:`bool`]
            Whether the bot should remove its own reactions.
            Default value is ``True``.
        case_insensitive: Optional[:class:`bool`]
            In addition to making normal commands case insensitive, attempts to
            normalize emojis by removing different skin colored and gendered
            modifiers when being invoked.

            Ex: 👍🏿/👍🏾/👍🏽/👍🏼/👍🏻 --> 👍 or 🧙‍♂️/🧙‍♀️ --> 🧙
    """
    pass


class AutoShardedReactionBot(ReactionBotMixin, commands.AutoShardedBot):
    """Sharded version of ReactionBot. IDK, probably works. Subclass of
    :class:`discord.ext.commands.AutoShardedBot`.
    """
    pass
