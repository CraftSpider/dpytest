"""
    Main module for supporting predicate-style assertions.
    Handles checking various state matches the desired outcome.

    All verify types should be re-exported at ``discord.ext.test``, this is the primary
    entry point for assertions in the library

    See also:
        :mod:`discord.ext.test.runner`
"""

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
    """
        Builder for message verifications. When done building, should be asserted.

        **Example**:
        ``assert dpytest.verify().message().content("Hello World!")``
    """

    _used: discord.Message | int | _Undef | None

    _contains: bool
    _peek: bool
    _nothing: bool
    _content: str | _Undef | None
    _embed: discord.Embed | _Undef | None
    _attachment: str | pathlib.Path | _Undef | None

    def __init__(self) -> None:
        self._used = _undefined

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

    def __str__(self) -> str:
        if self._used is not _Undef:
            return f"Expected {self._expectation()}, found {self._found}"
        else:
            return f"VerifyMessage(expects={self._expectation()})"

    def __bool__(self) -> bool:
        self._used = None

        if self._nothing:
            self._used = sent_queue.qsize()
            return sent_queue.qsize() == 0

        if self._peek:
            message: discord.Message = sent_queue.peek()
        else:
            try:
                message = sent_queue.get_nowait()
            except asyncio.QueueEmpty:
                # By now we're expecting a message, not getting one is a failure
                return False
        self._used = message

        return self._check_msg(message)

    def _expectation(self) -> str:
        if self._nothing:
            return "no messages"
        else:
            contains = "contains"
            content = f"content={self._content}" if self._content is not _Undef else ""
            embed = f"embed={self._embed}" if self._embed is not _Undef else ""
            attachment = f"attachment={self._attachment}" if self._attachment is not _Undef else ""
            event = " ".join(filter(lambda x: x, [contains, content, embed, attachment]))
            return f"message {event}"

    def _diff_msg(self) -> str:
        if self._nothing:
            return f"{self._used} messages"
        elif self._used is None:
            return "no message"
        else:
            return str(self._used)

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

    def contains(self) -> 'VerifyMessage':
        """
            Only check whether content/embed list/etc contain the desired input, not that they necessarily match
            exactly

        :return: Self for chaining
        """
        self._contains = True
        return self

    def peek(self) -> 'VerifyMessage':
        """
            Don't remove the verified message from the queue

        :return: Self for chaining
        """
        self._peek = True
        return self

    def nothing(self) -> 'VerifyMessage':
        """
            Check that no message was sent

        :return: Self for chaining
        """
        if self._content is not _undefined or self._embed is not _undefined or self._attachment is not _undefined:
            raise ValueError("Verify nothing conflicts with verifying some content, embed, or attachment")
        self._nothing = True
        return self

    def content(self, content: str | None) -> 'VerifyMessage':
        """
            Check that the message content matches the input

        :param content: Content to match against, or None to ensure no content
        :return: Self for chaining
        """
        if self._nothing:
            raise ValueError("Verify content conflicts with verifying nothing")
        self._content = content
        return self

    def embed(self, embed: discord.Embed | None) -> 'VerifyMessage':
        """
            Check that the message embed matches the input

        :param embed: Embed to match against, or None to ensure no embed
        :return: Self for chaining
        """
        if self._nothing:
            raise ValueError("Verify embed conflicts with verifying nothing")
        self._embed = embed
        return self

    def attachment(self, attach: str | pathlib.Path | None) -> 'VerifyMessage':
        """
            Check that the message attachment matches the input

        :param attach: Attachment path to match against, or None to ensure no attachment
        :return: Self for chaining
        """
        if self._nothing:
            raise ValueError("Verify attachment conflicts with verifying nothing")
        self._attachment = attach
        return self


class VerifyActivity:
    """
        Builder for activity verifications. When done building, should be asserted

        **Example**:
        ``assert not dpytest.verify().activity().name("Foobar")``
    """

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

        if self._name is not _undefined and self._name != bot_act.name:
            return False
        if self._url is not _undefined and self._url != bot_act.url:
            return False
        if self._type is not _undefined and self._type != bot_act.type:
            return False

        return True

    def matches(self, activity) -> 'VerifyActivity':
        """
            Ensure that the bot activity exactly matches the passed activity. Most restrictive possible check.

        :param activity: Activity to compare against
        :return: Self for chaining
        """
        if self._name is not _undefined or self._url is not _undefined or self._type is not _undefined:
            raise ValueError("Verify exact match conflicts with verifying attributes")
        self._activity = activity
        return self

    def name(self, name: str) -> 'VerifyActivity':
        """
            Check that the activity name matches the input

        :param name: Name to match against
        :return: Self for chaining
        """
        if self._activity is not _undefined:
            raise ValueError("Verify name conflicts with verifying exact match")
        self._name = name
        return self

    def url(self, url: str) -> 'VerifyActivity':
        """
            Check the the activity url matches the input

        :param url: Url to match against
        :return: Self for chaining
        """
        if self._activity is not _undefined:
            raise ValueError("Verify url conflicts with verifying exact match")
        self._url = url
        return self

    def type(self, type: discord.ActivityType) -> 'VerifyActivity':
        """
            Check the activity type matches the input

        :param type: Type to match against
        :return: Self for chaining
        """
        if self._activity is not _undefined:
            raise ValueError("Verify type conflicts with verifying exact match")
        self._type = type
        return self


class Verify:
    """
        Base for all kinds of verification builders. Used as an
        intermediate step for the return of verify().
    """

    def __init__(self):
        pass

    def message(self) -> VerifyMessage:
        """
            Verify a message

        :return: Message verification builder
        """
        return VerifyMessage()

    def activity(self) -> VerifyActivity:
        """
            Verify the bot's activity

        :return: Activity verification builder
        """
        return VerifyActivity()


def verify() -> Verify:
    """
        Verification entry point. Call to begin building a verification.

        **Warning**: All verification builders do nothing until asserted, used in an if statement,
        or otherwise converted into a bool. They will raise RuntimeWarning if this isn't done to help
        catch possible errors.

    :return: Verification builder
    """
    return Verify()
