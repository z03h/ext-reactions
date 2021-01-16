import re

#skin colors, genders
_to_clean = re.compile('\U0001f3fb|\U0001f3fc|\U0001f3fd|\U0001f3fe|\U0001f3ff|' \
                       '\u200d[\u2642\u2640]\ufe0f')

def scrub_emoji(emoji, *, repl=''):
    """Uses regex to replace skin color modifiers and gender modifiers with
    empty string.

    Ex: 👍🏿/👍🏾/👍🏽/👍🏼/👍🏻 --> 👍 or 🧙‍♂️/🧙‍♀️ --> 🧙

    Parameters
    ----------
    emoji: :class:`str`
        the emoji to remove modifiers from
    repl: Union[:class:`str`, Callable]
        ``repl`` to pass :func:`re.sub`

    Returns
    --------
    :class:`str`
        the input text scrubbed of modifiers
    """
    return _to_clean.sub(repl, emoji)
