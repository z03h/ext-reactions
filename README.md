# ReactionCommandBot
Bot that only listens to reactions for commands
Listens for `command_emoji`, then add reactions to invoke a command

Use `ReactionBotBase(command_emoji, listening_emoji, *args, timeout=10, **kwargs)` to create it.
`args`/`kwargs` are the same for normal `commands.Bot` except `command_prefix` doesn't do anything
- `command_emoji` is similar to command prefix, all command invokes must start with this emoji
- `listening_emoji` is the emoji to let the user know the bot is listening for emojis
- `timeout` is the time in seconds to listen for emojis after `command_emoji`
- `emoji_mapping` is a dict of `emoji: ReactionCommand`. Filled automatically when commands are added

No support for groups, only commands.
You have to use `@reaction_command(emoji)`  or `@bot.command([emoji1, emoji2])`.

You can use multiple emojis for each command, such as

- single string of multiple emojis
> `@bot.command('\N{REGIONAL INDICATOR SYMBOL LETTER A}\N{REGIONAL INDICATOR SYMBOL LETTER B}')`

or

- a list with multiple strings of emojis
> `@bot.command(['\N{REGIONAL INDICATOR SYMBOL LETTER A}', '\N{REGIONAL INDICATOR SYMBOL LETTER B}'])`

### Things to note when using this:
- No group support. Should only use `ReactionCommand`, but have only added things to it though (I think)
  - can get the emojis to invoke the command with `ReactionCommand.emojis`
  - no option to have arguments since reactions only, maybe later
- modified `DefaultHelpCommand` in the form of `ReactionHelp` that shows emojis along with commands
- cut down `ReactionContext` compared to normal `Context`. Doesn't have the full `message` and other broken methods because of that
  - `ReactionContext.message` has `id`, `channel`, `guild` set. `author` is set to the user who added reactions
    - you can get the message the reactions were added to by fetching `ReactionContext.message.id` from `ReactionContext.channel`
  - most methods like `ReactionContext.send`/`ReactionContext.author` should still work
