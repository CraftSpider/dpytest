# History

## 0.7.0

⚠️ Warning ⚠️:

This can be **breaking** :

The `configure` function has changed.
It nows accepts either an `int` (like in the previous version) OR a `list` of `string` for the parameters `guilds`, `text_channels`, `voice_channels` and `members`.
But the names of the parameters had to be changed.

`num_guilds`, `num_text_channels`, `num_voice_channels`, `num_members` are DERECATED.

Example:

```python
    dpytest.configure(bot,
                      guilds=["CoolGuild", "LameGuild"],
                      text_channels=["Fruits", "Videogames"],
                      voice_channels=2,
                      members=["Joe", "Jack", "William", "Averell"])
```

Other changes:

- fixes in typing
- add `content_type` to `dict_from_attachment()`

## 0.6.8

Test agains discord.py 2.3

## 0.6.7

Fix bug in channel_history

Fix issue #111

## 0.6.6

Support asyncio tasks that have no \_\_name\_\_

## 0.6.5

This release allows testing with Voice Channels.

New :

- `FakeVoiceChannel` and `FakeVoiceClient` classes implemetation
- New tests

Changes :

- `create_channel` method can create voice channel

⚠️ Warning ⚠️:

This can be **breaking** :

the `configure()` function DOESN'T take the keyword parameter `num_channels` anymore, but instead :
`num_text_channels` and `num_voice_channels`

## 0.6.4

- Fix: edit message doesn't update message queue
- Refactor **init**.py import to be explicit exports as per PEP 484

## 0.6.3

- Update requirements for discord.py 2.2.2

## 0.6.2

This is the version for discord.py 2.2.0

- Embed equality check now checks for equality of fields.
- Fix members factories to add the "flags" key (necessary in 2.2.0)

## 0.6.1

- Linting

## 0.6.0

- First version for working with dpytest>=2.X.X
    Changes have been made in backend, factories, websocket
- Change the README
- Change the setup.py for python >= 3.8
- Changing in doc

## 0.5.3

- Docs: Add vertical spacing for functions & methods
- Fix behaviour 'discord.Role.edit' with hoist, mentionable, etc.

## 0.5.2

- Get member mentions by using the user ID in mention

## 0.5.1

- NEW methods : Pins, get_user, & clear_reactions
- fix utils functions imports

## 0.5.0

- Remove the runner verification methods, replace them with verification builders

## 0.4.0

- Rename simulate_reaction -> add_reaction and make it take a user to react as

## 0.3.0

- unrealease (error when bumping version)

## 0.2.0

- Merge hint files into .py files
- Use typing export of Pattern

## 0.1.1

- Add content type to attachments
- Overwrite _guild_needs_chunking (fix for asyncio wait_for errors)

## 0.1.0

- Bump version (sould have done that with 0.0.23, since many changes have been commited)
- Bug fix with role_mentions=None being not iterable.

## 0.0.23

- Support for discord.py 1.7.1
- Attachments allowed on messages
- verify_embed without test fixed
- Add members intent
- Added more testing
