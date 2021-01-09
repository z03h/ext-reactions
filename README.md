# Reaction Command Bot
Bot that can listen to reactions for commands.
***
`ReactionBotBase(command_prefix, command_emoji, listening_emoji, *args, timeout=10, **kwargs)`
- `args`/`kwargs` are the same as `commands.Bot`
  - `case_insensitive` tries to ignore different skin color/gendered emojis
- `command_emoji` is similar to command prefix, all command invokes must start with this emoji
- `listening_emoji` is the emoji to let the user know the bot is listening for emojis
- `timeout` is the time in seconds to listen for emojis after `command_emoji`. Timer will reset after each added emoji
Added `ReactionBotBase` things
- `emoji_mapping` is a dict of `emoji: ReactionCommand`
- `get_emoji_command(str)` gets which command emojis `str` map to
- `process_reaction_commands(payload, cls=ReactionContext)` creates and invokes Context of type `cls` if `command_emoji` is reacted
- `wait_emoji_stream(user_id, msg_id)` waits for reactions from user on message and returns them as a string

1. Listens for `command_emoji` added, then waits_for reactions from that user on that message
2. Will listen for raw reaction add and remove
3. After `timeout` seconds or user removes `command_emoji`, ends the wait_for
4. Joins all the reactions into a single string and gets the command from `emoji_mapping`
***
Create `ReactionCommand`'s with `@reaction_command(emoji)` in cogs or `@bot.reaction_command([emoji1, emoji2])`.

You can use multiple emojis for each command

- single string of emoji(s), user must add emojis in order to invoke the command
> `@reaction_command('\N{REGIONAL INDICATOR SYMBOL LETTER A}\N{REGIONAL INDICATOR SYMBOL LETTER B}')`

- a list with multiple strings of emojis, like aliases
> `@bot.reaction_command(['\N{REGIONAL INDICATOR SYMBOL LETTER A}', '\N{REGIONAL INDICATOR SYMBOL LETTER B}'])`
***
### Things to note when using this:
- `ReactionCommand` should work like normal commands in addition to reaction invoke
  - can get the emojis to invoke the command with `ReactionCommand.emojis`
  - no converting or arguments. All args and kwargs will be `None` when invoked from reactions
- modified `DefaultHelpCommand` in the form of `ReactionHelp` that shows emojis along with commands
  - default `ReactionHelp` emoji is `'\N{REGIONAL INDICATOR SYMBOL LETTER H}'`
- cut down `ReactionContext` compared to normal `Context`. Doesn't have the full `message` and has broken methods because of that
  - `ReactionContext.message` has `id`, `channel`, `guild` attributes. `author` is set to the user who added reactions
    - `author` will be a `discord.Object` with id of user who reacted if `get_member` or `get_user` fail
    - you can get the message the reactions were added to by fetching `ReactionContext.message.id` from `ReactionContext.channel`
  - most methods/attributes like `ReactionContext.send`/`ReactionContext.channel` should still work
  - check `reaction_command` attribute on `Context` and `ReactionContext` if invoke from reactions or message
