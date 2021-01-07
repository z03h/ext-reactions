# Reaction Command Bot
Bot that can listen to reactions for commands
***
Use `ReactionBotBase(command_emoji, listening_emoji, *args, timeout=10, **kwargs)`.
- `args`/`kwargs` are the same as `commands.Bot`
  - `case_insensitive` tries to ignore different skin color/gendered emojis
- `command_emoji` is similar to command prefix, all command invokes must start with this emoji
- `listening_emoji` is the emoji to let the user know the bot is listening for emojis, can be `None`
- `timeout` is the time in seconds to listen for emojis after `command_emoji`. Timer will reset after reach added emoji
- `emoji_mapping` is a dict of `emoji: ReactionCommand`

1. Listens for `command_emoji` added, then waits_for reactions from that user on that message
2. Will listen for reaction add and remove
3. After `timeout` seconds or user removes `command_emoji`, ends the wait_for
4. Joins all the reactions into a single string and gets the command from `emoji_mapping`
***
You have to use `@reaction_command(emoji)` in cogs or `@bot.emoji_command([emoji1, emoji2])`.

You can use multiple emojis for each command

- single string of emoji(s), user must add emojis in order to invoke the command
> `@reaction_command('\N{REGIONAL INDICATOR SYMBOL LETTER A}\N{REGIONAL INDICATOR SYMBOL LETTER B}')`

- a list with multiple strings of emojis, like aliases
> `@bot.emoji_command(['\N{REGIONAL INDICATOR SYMBOL LETTER A}', '\N{REGIONAL INDICATOR SYMBOL LETTER B}'])`
***
### Things to note when using this:
- Should only use `ReactionCommand`, but have only added things to it though (I think)
  - can get the emojis to invoke the command with `ReactionCommand.emojis`
  - no option to have arguments since reactions only
- modified `DefaultHelpCommand` in the form of `ReactionHelp` that shows emojis along with commands
  - default `ReactionHelp` emoji is `'\N{REGIONAL INDICATOR SYMBOL LETTER H}'`
- cut down `ReactionContext` compared to normal `Context`. Doesn't have the full `message` and has broken methods because of that
  - `ReactionContext.message` has `id`, `channel`, `guild` attributes. `author` is set to the user who added reactions
    - you can get the message the reactions were added to by fetching `ReactionContext.message.id` from `ReactionContext.channel`
  - most methods like `ReactionContext.send`/`ReactionContext.author` should still work
