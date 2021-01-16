import discord
from discord.ext import commands

__all__ = ('ReactionContext',)

class ReactionContext(commands.Context):
    """It's a context, ye...

    I do some f**ked up sh*t here so.

    Attributes
    ----------
    author: Union[:class:`discord.Member`, :class:`discord.User`, :class:`.ProxyBase`]

        .. Warning::
            This is **not the message author**. It is the user who added reactions.

    payload: Union[:class:`.ProxyPayload`, :class:`discord.RawReactionActionEvent`]
        The payload this context came from, type depends on if this context
        came from raw method or not.
    message: Union[:class:`discord.Message`, :class:`discord.PartialMessage`]
        Will be a full :class:`discord.Message` if not from a raw event.

        .. Warning::
            There's no full message from :class:`payload <discord.RawReactionActionEvent>`,
            so ``ctx.message`` is a :class:`discord.PartialMessage`. This
            PartialMessage's ``channel`` and ``guild`` attributes might be
            a :class:`.ProxyBase` and becuase of that ``ctx.channel``
            and ``ctx.guild`` might also be.

            Use :meth:`.get` or :meth:`.fetch` to get the full message.

    reaction_command: :class:`bool`
        Whether this ctx was invoked from reactions
    full_emojis: :class:`str`
        String of all the emojis (except prefix and listening_emojis)
        that the user added or removed.
    listening_emoji: Optional[:class:`str`]
        The listening emoji that was used with this ctx
    remove_after: list[tuple[:class:`str`, :class:`discord.User`]]
        Tuples of emoji and the user to remove after command invoke.

        List of tuples. Tuples are ``(emoji, user)``
    """

    def __init__(self, bot, payload, author, **attrs):
        self.bot = bot
        # bot is the only guarateed thing here
        # since all the proxies get state from bot
        self._state = bot._connection

        self.prefix = attrs.pop('prefix', None)
        self.command = attrs.pop('command', None)
        self.message = attrs.pop('message', None)
        self.args = attrs.pop('args', [])
        self.kwargs = attrs.pop('kwargs', {})
        self.view = attrs.pop('view', None)
        self.invoked_with = attrs.pop('invoked_with', None)
        self.invoked_subcommand = attrs.pop('invoked_subcommand', None)
        self.subcommand_passed = attrs.pop('subcommand_passed', None)
        self.command_failed = attrs.pop('command_failed', False)

        # ReactionContext specific attributes
        self.payload = payload
        self.reaction_command = True
        self.remove_after = []
        self.listening_emoji = None
        self.full_emojis = ''
        # need to separate ctx.author from ctx.message.author
        # since they can be different users
        self.author = author

    async def fetch(self):
        """Shortcut to :meth:`ctx.message.fetch() <discord.PartialMessage.fetch>`.

        Updates :attr:`.ReactionContext.message` with the fetched message and returns it.

        Raises
        ------
        :exc:`discord.HTTPException`
            Fetching the message failed

        Returns
        -------
        :class:`discord.Message`
            The message the PartialMessage was representing.
        """
        if self.message is None or isinstance(self.message, discord.Message):
            return self.message
        self.message = await self.message.fetch()
        return self.message

    def get(self, *, reverse=True):
        """Searches :attr:`Bot.cached_messages <discord.ext.commands.Bot.cached_messages>`
        for a message where ``ctx.message.id == message.id``. Returns ``None``
        if the message was not found.

        If found, updates :attr:`.ReactionContext.message` with the message and
        returns it.

        Parameters
        ----------
        reverse: :class:`bool`
            Whether should search :func:`reversed` ``cached_messages`` (newest
            messages first). Defaults to ``True``.

        Returns
        -------
        Optional[:class:`discord.Message`]
            The message or ``None``
        """
        if self.message is None or isinstance(self.message, discord.Message):
            return self.message
        m = self.bot._get_message(self.message.id, reverse=reverse)
        if m:
            self.message = m
        return m
