
import typing
import asyncio
import pathlib
import discord

from .runner import sent_queue
from .utils import embed_eq


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

    def __init__(self):
        self._invert = False
        self._contains = False
        self._peek = False
        self._nothing = False
        self._content = _undefined
        self._embed = _undefined
        self._attachment = _undefined

    def __bool__(self):
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

    def _check_msg(self, msg: discord.Message):
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
            elif self._content != msg.content:
                return False
        # TODO: Support contains for these two below, 'contains' should mean 'any number of which one matches',
        #       while 'exact' should be 'only one which must match'
        if self._embed is not None and self._embed is not _undefined:
            if not embed_eq(self._embed, msg.embeds[0]):
                return False
        if self._attachment is not None and self._attachment is not _undefined:
            import urllib.request as request
            print("Filename: {}".format(msg.attachments[0].filename))
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


class Verify:

    def __init__(self):
        pass

    def message(self) -> VerifyMessage:
        return VerifyMessage()


def verify() -> Verify:
    return Verify()
