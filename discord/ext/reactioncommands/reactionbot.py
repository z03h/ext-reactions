import time
import asyncio
import traceback
from collections import Counter

import discord
from discord.ext import commands

from .reactionhelp import ReactionHelp
from .reactioncontext import ReactionContext
from .reactioncore import ReactionCommandMixin, ReactionGroupMixin
from .reactionproxy import (ProxyUser, ProxyMember, ProxyTextChannel,
                            ProxyDMChannel, ProxyGuild, ProxyPayload)

__all__ = ('ReactionBot', 'AutoShardedReactionBot', 'ReactionBotMixin')


class ReactionBotMixin(ReactionGroupMixin):
    """Mixin for implementing reaction commands to Bot"""
    def __init__(self, command_prefix, prefix_emoji, listening_emoji, *args,
                 listen_timeout=15, listen_total_timeout=120, remove_reactions_after=True,
                 **kwargs):
        self.prefix_emoji = prefix_emoji
        self.listening_emoji = listening_emoji
        self.listen_timeout = listen_timeout
        self.listen_total_timeout = listen_total_timeout
        self._active_ctx_sessions = Counter()
        self.remove_reactions_after = remove_reactions_after
        self._debug_ = kwargs.get('_debug', False)
        self._mc = commands.MaxConcurrency(1, per=commands.BucketType.user, wait=False)

        kwargs.setdefault('help_command', ReactionHelp())
        super().__init__(command_prefix=command_prefix, *args, **kwargs)

    async def get_context(self, message, *, cls=commands.Context):
        """Functions exactly the same as original :meth:`~discord.ext.commands.Bot.get_context`.

        Only difference is this function will attempt to set attribute
        ``ctx.reaction_command`` to ``False`` to indicate it is a message command.

        Returns
        -------
        :class:`~discord.ext.commands.Context`
            The context from message
        """
        ctx = await super().get_context(message, cls=cls)
        try:
            ctx.reaction_command = False
        except AttributeError as e:
            if self._debug_:
                print('failed to set ctx.reaction_command\n', e)
        return ctx

    async def on_raw_reaction_add(self, payload):
        await self.process_raw_reaction_commands(payload)

    def _get_message(self, message_id, *, reverse=True):
        """Searches :attr:`.cached_messages` for a message with id
        ``message_id``.

        Parameters
        ----------
        message_id: :class:`int`
            id of the message to search for
        reverse: :class:`bool`
            Whether it should search reversed (newest first). Default value is
            ``True``

        Returns
        -------
        Optional[:class:`discord.Message`]
            The message or ``None``
        """
        messages = self.cached_messages if not reverse else reversed(self.cached_messages)
        return discord.utils.get(messagess, id=message_id) if self._connection._messages else None

    async def _get_x_emoji(self, payload, *, attr, single=False):
        emoji = ret = getattr(self, attr)
        if callable(emoji):
            ret = await discord.utils.maybe_coroutine(emoji, self, payload)

        if not isinstance(ret, str):
            if single:
                raise TypeError(f"{attr} must be plain string, or None"
                                f"returning either of these, not {ret.__class__.__name__}")
            try:
                ret = list(ret)
            except TypeError:
                # It's possible that a generator raised this exception.  Don't
                # replace it with our own error if that's the case.
                if isinstance(ret, collections.abc.Iterable):
                    raise

                raise TypeError(f"{attr} must be plain string, iterable of strings, or callable "
                                f"returning either of these, not {ret.__class__.__name__}")

            if not ret:
                raise ValueError(f"Iterable {name} must contain at least one prefix")

        return ret

    async def get_prefix_emoji(self, payload):
        """Method that gets the :attr:`.ReactionBot.prefix_emoji` or list of
        emojis that can be used to start listening for commands.

        Reaction mirror to :meth:`~discord.ext.commands.Bot.get_prefix`.

        You can try using :meth:`.ProxyPayload.from_reaction_user` to use this
        with non raw reaction methods or :meth:`~.ProxyPayload.from_message`
        for a message.

        Parameters
        ----------
        payload: :class:`discord.RawReactionActionEvent`
            payload to get prefix emoji from

        Returns
        -------
        Union[:class:`list`, :class:`str`]
            A list of emojis, or single emoji that the bot is
            listening for.
        """
        return await self._get_x_emoji(payload, attr='prefix_emoji')

    async def get_listening_emoji(self, payload):
        """Method that gets :attr:`.listening_emoji` that is used for group invoke
        and letting the user know the bot is listening.

        You can try using :meth:`.ProxyPayload.from_reaction_user` to use this
        with non raw reaction methods or :meth:`~.ProxyPayload.from_message`
        for a message.

        Parameters
        ----------
        payload: :class:`discord.RawReactionActionEvent`
            payload to get listening_emoji from

        Returns
        -------
        Optional[:class:`str`]
            A single emoji or ``None``. If not ``None`` the bot
            will add as a reaction to indicate it is listening for reactions.
        """
        if self.listening_emoji is None:
            return None
        return await self._get_x_emoji(payload, attr='listening_emoji', single=True)

    async def get_reaction_context(self, reaction, user, *, cls=ReactionContext, check=None, event_type=None):
        """Creates a context from :class:`~discord.Reaction` and
        :class:`discord.User`/:class:`discord.Member`.

        Meant to be used with :func:`~discord.on_reaction_add` or
        :func:`~discord.on_reaction_remove`.

        Reaction mirror to :meth:`~discord.ext.commands.Bot.get_context`.

        Parameters
        ----------
        reaction: :class:`discosrd.Reaction`
            the reaction the user added
        user: Union[:class:`discord.Member`, :class:`discord.User`]
            the user who added the reaction
        cls:
            The class that will be used for the context.
        check: Optional[Callable[:class:`discord.RawReactionActionEvent`]]
            Check that will be passed to :meth:`~discord.ext.commands.Bot.wait_for`.
            Default check is equivalent to:

            .. code-block:: python

                def check(payload: discord.RawReactionActionEvent):
                    same_msg = payload.message_id == ctx.message.id
                    same_user =  payload.user_id == ctx.author.id
                    return same_msg and same_user

            .. note::

                This still uses raw methods to listen for reactions.

        Returns
        -------
        :class:`~.reactioncommands.ReactionContext`
            The context to invoke.
        """
        payload = ProxyPayload.from_reaction_user(reaction, user, event_type=event_type)
        ctx = cls(self, payload, author=user, message=reaction.message)
        return await self._start_ctx_session(ctx, check=check)

    async def get_raw_reaction_context(self, payload, *, cls=ReactionContext, check=None):
        """Creates a :class:`~.reactioncommands.ReactionContext` from
        :class:`payload <discord.RawReactionActionEvent>`.

        Meant to be used with :func:`~discord.on_raw_reaction_add` or
        :func:`~discord.on_raw_reaction_remove`

        A lot of weird sh*t happens here. If something is not cached or provided,
        a :class:`~discord.ext.reactioncommands.reactionproxy.ProxyBase`
        where  ``id`` may be used instead. It may have attributes
        set to other proxy objects. These proxy objects `should` behave similar
        to :class:`discord.PartialMessage`, but subclassed from their originals.
        Most methods should work but attributes probably won't.

        Raw Reaction mirror to :meth:`~discord.ext.commands.Bot.get_context`.

        Parameters
        ----------
        payload: :class:`discord.RawReactionActionEvent`
            payload to start getting context from
        cls:
            The class that will be used for the context.
        check: Optional[Callable[:class:`discord.RawReactionActionEvent`]]
            Check that will be passed to :meth:`~discord.ext.commands.Bot.wait_for`.
            Default check is equivalent to:

            .. code-block:: python

                def check(payload: discord.RawReactionActionEvent):
                    same_msg = payload.message_id == ctx.message.id
                    same_user =  payload.user_id == ctx.author.id
                    return same_msg and same_user

        Returns
        -------
        :class:`~.reactioncommands.ReactionContext`
            The context to invoke.
        """

        author, channel, guild = self._create_proxies(payload)
        message = channel.get_partial_message(payload.message_id)

        ctx = cls(self, payload, author=author, message=message)
        return await self._start_ctx_session(ctx, check=check)

    async def process_raw_reaction_commands(self, payload):
        """Gets context and invokes from a payload. Takes :class:`payload <discord.RawReactionActionEvent>`
        from :func:`~discord.on_raw_reaction_add` or
        :func:`~discord.on_raw_reaction_remove`.

        Raw Reaction mirror to :meth:`~discord.ext.commands.Bot.process_commands`.

        .. note::
            If you overwrite :func:`raw_reaction_add <discord.on_raw_reaction_add>`
            or use :meth:`discord.ext.commands.Bot.event` to overwrite,
            don't forget to add this so reaction commands will still work.

        Parameters
        ----------
        payload: :class:`discord.RawReactionActionEvent`
            Payload to get context and invoke from.
        """
        author = payload.member or self.get_user(payload.user_id)
        if author and author.bot:
            return
        context = await self.get_raw_reaction_context(payload)
        await self.invoke(context)

    async def process_reaction_commands(self, reaction, user):
        """Gets context and invokes from a reaction and user. Gets arguments from
        from :func:`~discord.on_reaction_add` or :func:`~discord.on_reaction_remove`.

        Reaction mirror to :meth:`~discord.ext.commands.Bot.process_commands`.

        Parameters
        ----------
        reaction: :class:`discord.Reaction`
            The reaction the user added
        user: Union[:class:`discord.Member`, :class:`discord.User`]
            The user who added the reaction
        """
        if user.bot:
            return
        context = await self.get_reaction_context(reaction, user)
        await self.invoke(context)

    def _create_proxies(self, payload):
        """Gets relevant ctx attributes from cache or creates
        :class:`~discord.ext.commands.reactioncommands.reactionproxy.ProxyBase`
        instead using payload as context.
        """
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

    async def _start_ctx_session(self, ctx, *, check):
        """Sets attributes of ctx and starts _early_invoke or listening session.

        Parameters
        ----------
        ctx: :class:`~discord.ext.reactioncommands.ReactionContext`
            the context to fill out
        check: Callable
            check to be passed to :meth:`~discord.commands.ext.Bot.wait_for`

        Returns
        -------
        :class:`~discord.ext.reactioncommands.ReactionContext`
            returns the ctx that was passed in with attributes filled out
        """
        maybe_prefix = str(ctx.payload.emoji)
        prefix_emoji = await self.get_prefix_emoji(ctx.payload)

        if (maybe_prefix == prefix_emoji or
                (isinstance(prefix_emoji, list) and maybe_prefix in prefix_emoji)):
            ctx.prefix = maybe_prefix
        else:
            # try to check if it's a command
            # that can be invoked without prefix
            if await self.reaction_before_processing(ctx, check_only=True):
                self._early_invoke(ctx, maybe_prefix)
            return ctx
        try:
            if not await self.reaction_before_processing(ctx):
                return ctx
            self._active_ctx_sessions[ctx.message.id] += 1
            try:
                emojis = await asyncio.wait_for(self._wait_for_emoji_stream(ctx, check=check),
                                                timeout=self.listen_total_timeout)
            except asyncio.TimeoutError:
                emojis = ''

            self._active_ctx_sessions[ctx.message.id] -= 1

            self.loop.create_task(self.reaction_after_processing(ctx))

            ctx.view = commands.view.StringView(emojis)
            ctx.full_emojis = emojis
            ctx.view.skip_ws()
            invoker = ctx.view.get_word()
            ctx.invoked_with = invoker
            ctx.command = self.get_reaction_command(invoker)
        except Exception as e:
            if self._debug_:
                traceback.print_exc()
        return ctx

    async def _wait_for_emoji_stream(self, ctx, *, check=None):
        """Helper method to listen to reactions added by a user and join them
        together into a string

        Parameters
        ----------
        ctx: :class:`~discord.ext.reactioncommands.ReactionContext`
            ctx that started this listening
        check: Callable
            check to be passed to ``wait_for` that listens to
            ``raw_reaction_add`` and ``raw_reaction_remove``

        Returns
        -------
        :class:`str`
            emojis joined together
        """
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
                except Exception as e:
                    if self._debug_:
                        print(e)
                    return ''
                emoji = str(payload.emoji)
                if emoji == ctx.prefix:
                    if command:
                        return ''.join(command)
                    else:
                        return ''
                elif emoji == ctx.listening_emoji:
                    command.append(' ')
                else:
                    command.append(emoji)
            else:
                #user stopped reacting, check if any reactions
                self._cleanup_reaction_tasks(done, pending)
                if command:
                    return ''.join(command)
                else:
                    return ''

    def _early_invoke(self, ctx, emoji):
        """Checks if user reacted for a command that can be invoked without
        reaction prefix. Sets appropriate ctx attributes

        Returns
        -------
        :class:`bool`:
            whether to without prefix
        """
        command = self.get_reaction_command(emoji)
        if command and command.invoke_without_prefix:
            emoji = str(ctx.payload.emoji)
            ctx.view = commands.view.StringView(emoji)
            ctx.full_emojis = ctx.view.get_word()
            ctx.invoked_with = emoji
            ctx.prefix = ctx.listening_emoji = None
            ctx.command = command
            return True
        return False

    def _cleanup_reaction_tasks(self, done, pending):
        # cleanup tasks from emoji waiting
        for future in (done or []):
            future.exception()
        for future in (pending or []):
            future.cancel()

    async def reaction_before_processing(self, ctx, *, check_only=False):
        """Method that is called after verifying the prefix emoji and before
        the command input is added by the user. Determines if the bot should
        listen to reactions. :attr:`.ReactionBot.listening_emoji` is added here.

        .. note::
            This method prevents users from starting multiple listening sessions
            and has some cleanup that is done in :meth:`.reaction_after_processing`.
            If you overwrite one you should probably overwrite the other /call
            ``super()``.

        Parameters
        ----------
        ctx: :class:`~.reactioncommands.ReactionContext`
            Context that may be invoked.
        check_only: :class:`bool`
            Whether this should be standalone call without an expected matching
            :meth:`~ReactionBot.reaction_after_processing` call. Default ``False``.

        Returns
        -------
         :class:`bool`
            Whether the bot should continue listening for reactions or not.
        """
        try:
            await self._mc.acquire(ctx)
        except commands.MaxConcurrencyReached:
            return False
        else:
            if check_only:
                await self._mc.release(ctx)
                return True

        listening_emoji = await self.get_listening_emoji(ctx.payload)
        ctx.listening_emoji = listening_emoji
        if listening_emoji is not None:
            try:
                await ctx.message.add_reaction(listening_emoji)
                ctx.remove_after.append((listening_emoji, ctx.me))
            except Exception as e:
                if self._debug_:
                    print('failed adding listening emoji', e)
        return True

    async def reaction_after_processing(self, ctx):
        """Method that is called after verifying the command and before checks,
        ``@before_invoke``, and command invoke. If :attr:`.ReactionBot.remove_reactions_after`
        is ``True``, they will be removed here.

        .. note::
            This method cleans up after :meth:`.reaction_before_processing`.
            If you overwrite one you should probably overwrite the other/call
            ``super()``.

        Parameters
        ----------
        ctx: :class:`~.reactioncommands.ReactionContext`
            Context that will be invoked.
        """
        await self._mc.release(ctx)
        if self.remove_reactions_after:
            try:
                can_remove = ctx.channel.permissions_for(ctx.me).manage_messages
            except:
                if self._debug_:
                    print('Error getting permissions in', ctx.channel)
                can_remove = False
            for emoji, user in ctx.remove_after:
                try:
                    if user == self.user:
                        if not (emoji == ctx.listening_emoji and self._active_ctx_sessions[ctx.message.id]):
                            await ctx.message.remove_reaction(emoji, self.user)
                    elif can_remove:
                        await ctx.message.remove_reaction(emoji, user)
                except discord.HTTPException:
                    pass
            if not self._active_ctx_sessions[ctx.message.id]:
                try:
                    del self._active_ctx_sessions[ctx.message.id]
                except KeyError:
                    pass


class ReactionBot(ReactionBotMixin, commands.Bot):
    """Subclass of :class:`discord.ext.commands.Bot` that adds reaction commands.

    All other ``args`` and ``kwargs`` should be the same as :class:`discord.ext.commands.Bot`.

    Attributes
    ----------
        prefix_emoji: Union[:class:`Callable`, :class:`list`, :class:`str`]
            Similar to command_prefix, but for starting emoji commands.
            Can be a string, list of strings, or callable/coroutine with the bot as its
            first parameter and :class:`discord.RawReactionActionEvent` as its
            second parameter. This callable should return a string or list of strings.
        listening_emoji: Union[:class:`Callable`, :class:`str`, :class:`None`]
            Same as prefix_emoji. Can be ``None`` if you don't want to invoke
            emoji groups with reactions or add a reaction on every
            :attr:`prefix_emoji` reaction.

            .. code-block:: python

                # example callable, bot.emoji_prefixes is a mapping of
                # guild id to emoji
                def prefix(bot, payload):
                    return bot.emoji_prefixes.get(payload.guild_id, "🤖")

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
        emoji_insensitive: Optional[:class:`bool`]
            Attempts to normalize emojis by removing different skin colored and
            gendered modifiers when being invoked.

            Ex: 👍🏿/👍🏾/👍🏽/👍🏼/👍🏻 --> 👍

            🧙‍♂️/🧙‍♀️ --> 🧙
    """
    pass


class AutoShardedReactionBot(ReactionBotMixin, commands.AutoShardedBot):
    """Sharded version of ReactionBot. IDK, probably works. Subclass of
    :class:`discord.ext.commands.AutoShardedBot`.
    """
    pass
