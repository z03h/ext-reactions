import re

#skin colors, male/female symbol, man/woman
_to_clean = re.compile('\U0001f3fb|\U0001f3fc|\U0001f3fd|\U0001f3fe|\U0001f3ff|' \
                       '\u200d[\u2642\u2640]\ufe0f|'\
                       '[\U0001f469\U0001f468]')

def scrub_emoji(emoji):
    """Uses regex to remove skin color modifiers and gender modifiers.

    Ex: 👍🏿/👍🏾/👍🏽/👍🏼/👍🏻 --> 👍

    🧙‍♂️/🧙‍♀️ --> 🧙

    Parameters
    ----------
    emoji: :class:`str`
        the emoji to remove modifiers from

    Returns
    --------
    :class:`str`
        the input text scrubbed of modifiers
    """
    def repl(m):
        #replace MAN/WOMAN with ADULT
        if m[0] in '\U0001f469\U0001f468':
            return '\U0001f9d1'
        return ''
    return _to_clean.sub(repl, emoji)
