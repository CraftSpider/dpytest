
import typing
import asyncio
import pathlib
import discord

from .runner import sent_queue, get_config
from .utils import embed_eq, activity_eq


class _Undef:

    _singleton = None

    def __new__(cls):
        if cls._singleton is None:
            cls._singleton = super().__new__(cls)
        return cls._singleton

    def __eq__(self, other):
        return self is other


_undefined = _Undef()


class VerifyMessage:

    _invert: bool
    _contains: bool
    _peek: bool
    _nothing: bool
    _content: typing.Union[None, _Undef, str]
    _embed: typing.Union[None, _Undef, discord.Embed]
    _attachment: typing.Union[None, _Undef, str, pathlib.Path]

    def __init__(self) -> None:
        self._used = False

        self._invert = False
        self._contains = False
        self._peek = False
        self._nothing = False
        self._content = _undefined
        self._embed = _undefined
        self._attachment = _undefined

    def __del__(self) -> None:
        if not self._used:
            import warnings
            warnings.warn("VerifyMessage dropped without being used, did you forget an `assert`?", RuntimeWarning)

    def __bool__(self) -> bool:
        self._used = True

        if self._nothing:
            return sent_queue.qsize() != 0 if self._invert else sent_queue.qsize() == 0

        if self._peek:
            message: discord.Message = sent_queue.peek()
        else:
            try:
                message = sent_queue.get_nowait()
            except asyncio.QueueEmpty:
                # By now we're expecting a message, not getting one is a failure
                return False

        result = self._check_msg(message)
        if self._invert:
            result = not result

        return result

    def _check_msg(self, msg: discord.Message) -> bool:
        # If any attributes are 'None', check that they don't exist
        if self._content is None and msg.content != "":
            return False
        if self._embed is None and msg.embeds:
            return False
        if self._attachment is None and msg.attachments:
            return False

        # For any attributes that aren't None or _undefined, check that they match
        if self._content is not None and self._content is not _undefined:
            if self._contains and self._content not in msg.content:
                return False
            if not self._contains and self._content != msg.content:
                return False
        if self._embed is not None and self._embed is not _undefined:
            if self._contains and not any(map(lambda e: embed_eq(self._embed, e), msg.embeds)):
                return False
            if not self._contains and (len(msg.embeds) != 1 or not embed_eq(self._embed, msg.embeds[0])):
                return False
        # TODO: Support contains for attachments, 'contains' should mean 'any number of which one matches',
        #       while 'exact' should be 'only one which must match'
        if self._attachment is not None and self._attachment is not _undefined:
            import urllib.request as request
            with open(self._attachment, "rb") as file:
                expected = file.read()
            # Generally, the URLs should be `file://` URLs, but this will work fine if they actually point elsewhere
            real = request.urlopen(msg.attachments[0].url).read()
            if expected != real:
                return False

        # Nothing failed, so we must match the message
        return True

    def not_(self) -> 'VerifyMessage':
        self._invert = True
        return self

    def contains(self) -> 'VerifyMessage':
        self._contains = True
        return self

    def peek(self) -> 'VerifyMessage':
        self._peek = True
        return self

    def nothing(self) -> 'VerifyMessage':
        if self._content is not _undefined or self._embed is not _undefined or self._attachment is not _undefined:
            raise ValueError("Verify nothing conflicts with verifying some content, embed, or attachment")
        self._nothing = True
        return self

    def content(self, content: typing.Optional[str]) -> 'VerifyMessage':
        if self._nothing:
            raise ValueError("Verify content conflicts with verifying nothing")
        self._content = content
        return self

    def embed(self, embed: typing.Optional[discord.Embed]) -> 'VerifyMessage':
        if self._nothing:
            raise ValueError("Verify embed conflicts with verifying nothing")
        self._embed = embed
        return self

    def attachment(self, attach: typing.Optional[typing.Union[str, pathlib.Path]]) -> 'VerifyMessage':
        if self._nothing:
            raise ValueError("Verify attachment conflicts with verifying nothing")
        self._attachment = attach
        return self


class VerifyActivity:

    def __init__(self) -> None:
        self._used = False

        self._activity = _undefined
        self._name = _undefined
        self._url = _undefined
        self._type = _undefined

    def __del__(self) -> None:
        if not self._used:
            import warnings
            warnings.warn("VerifyActivity dropped without being used, did you forget an `assert`?", RuntimeWarning)

    def __bool__(self) -> bool:
        self._used = True

        bot_act = get_config().guilds[0].me.activity

        if self._activity is not _undefined:
            return activity_eq(self._activity, bot_act)

        if self._name is not _undefined:
            if self._name != bot_act.name:
                return False
        if self._url is not _undefined:
            if self._url != bot_act.url:
                return False
        if self._type is not _undefined:
            if self._type != bot_act.type:
                return False

        return True

    def matches(self, activity) -> 'VerifyActivity':
        if self._name is not _undefined or self._url is not _undefined or self._type is not _undefined:
            raise ValueError("Verify exact match conflicts with verifying attributes")
        self._activity = activity
        return self

    def name(self, name: str) -> 'VerifyActivity':
        if self._activity is not _undefined:
            raise ValueError("Verify name conflicts with verifying exact match")
        self._name = name
        return self

    def url(self, url: str) -> 'VerifyActivity':
        if self._activity is not _undefined:
            raise ValueError("Verify url conflicts with verifying exact match")
        self._url = url
        return self

    def type(self, type: discord.ActivityType) -> 'VerifyActivity':
        if self._activity is not _undefined:
            raise ValueError("Verify type conflicts with verifying exact match")
        self._type = type
        return self


class Verify:

    def __init__(self):
        pass

    def message(self) -> VerifyMessage:
        return VerifyMessage()

    def activity(self) -> VerifyActivity:
        return VerifyActivity()


def verify() -> Verify:
    return Verify()
