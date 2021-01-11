import re

#skin colors, genders
_to_remove = '\U0001f3fb|\U0001f3fc|\U0001f3fd|\U0001f3fe|\U0001f3ff|' \
            '\u200d[\u2642\u2640]\ufe0f'
_to_clean = re.compile(_to_remove)

def scrub_emoji(emoji, *, repl=''):
    return _to_clean.sub(repl, emoji)
