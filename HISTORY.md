# History

## 0.6.4

- Fix: edit message doesn't update message queue
- Refactor __init__.py import to be explicit exports as per PEP 484

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
