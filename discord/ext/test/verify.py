"""
    Main module for supporting predicate-style assertions.
    Handles checking various state matches the desired outcome.

    All verify types should be re-exported at ``discord.ext.test``, this is the primary
    entry point for assertions in the library

    See also:
        :mod:`discord.ext.test.runner`
"""

import asyncio
import pathlib
from typing import TypeVar, Callable

import discord

from .runner import sent_queue, get_config
from .utils import embed_eq, activity_eq
from ._types import Undef, undefined


def _msg_to_str(msg: discord.Message) -> str:
    author = f"author=\"{msg.author.name}\""
    out = [author]
    if msg.content:
        out.append(f"content=\"{msg.content}\"")
    if msg.embeds:
        embeds = ", ".join(map(lambda e: str(e.to_dict()), msg.embeds))
        out.append(f"embeds=[{embeds}]")
    if msg.attachments:
        attachments = ", ".join(map(lambda a: a.filename, msg.attachments))
        out.append(f"attachments=[{attachments}]")
    inner = " ".join(out)
    return f"Message({inner})"


T = TypeVar('T')


def opt_undef_or(start: str, v: T | Undef | None, f: Callable[[T], str]) -> str:
    if v is undefined:
        return ""
    elif v is None:
        return f"{start}=Empty"
    else:
        return f"{start}={f(v)}"


class VerifyMessage:
    """
        Builder for message verifications. When done building, should be asserted.

        **Example**:
        ``assert dpytest.verify().message().content("Hello World!")``
    """

    _used: discord.Message | int | Undef | None

    _contains: bool
    _peek: bool
    _nothing: bool
    _content: str | Undef | None
    _embed: discord.Embed | Undef | None
    _attachment: str | pathlib.Path | Undef | None

    def __init__(self) -> None:
        self._used = undefined

        self._contains = False
        self._peek = False
        self._nothing = False
        self._content = undefined
        self._embed = undefined
        self._attachment = undefined

    def __del__(self) -> None:
        if not self._used:
            import warnings
            warnings.warn("VerifyMessage dropped without being used, did you forget an `assert`?", RuntimeWarning)

    def __repr__(self) -> str:
        if self._used is not undefined:
            return f"<VerifyMessage expected=[{self._expectation()}] found=[{self._diff_msg()}]>"
        else:
            return f"<VerifyMessage expected=[{self._expectation()}]>"

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
            content = opt_undef_or("content", self._content, lambda x: f'"{x}"')
            embed = opt_undef_or("embed", self._embed, lambda x: str(x.to_dict()))
            attachment = opt_undef_or("attachment", self._attachment, lambda x: str(x))
            event = " ".join(filter(lambda x: x, [contains, content, embed, attachment]))
            return f"{event}"

    def _diff_msg(self) -> str:
        if isinstance(self._used, int):
            return f"{self._used} messages"
        elif isinstance(self._used, discord.Message):
            return f"{_msg_to_str(self._used)}"
        elif self._used is None:
            return "no message"
        return ""

    def _check_msg(self, msg: discord.Message) -> bool:
        # If any attributes are 'None', check that they don't exist
        if self._content is None and msg.content != "":
            return False
        if self._embed is None and msg.embeds:
            return False
        if self._attachment is None and msg.attachments:
            return False

        # For any attributes that aren't None or undefined, check that they match
        if self._content is not None and self._content is not undefined:
            if self._contains and self._content not in msg.content:
                return False
            if not self._contains and self._content != msg.content:
                return False
        _embed = self._embed
        if _embed is not None and _embed is not undefined:
            if self._contains and not any(map(lambda e: embed_eq(_embed, e), msg.embeds)):
                return False
            if not self._contains and (len(msg.embeds) != 1 or not embed_eq(_embed, msg.embeds[0])):
                return False
        # TODO: Support contains for attachments, 'contains' should mean 'any number of which one matches',
        #       while 'exact' should be 'only one which must match'
        if self._attachment is not None and self._attachment is not undefined:
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
        if self._content is not undefined or self._embed is not undefined or self._attachment is not undefined:
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

    _activity: discord.activity.ActivityTypes | None | Undef
    _name: str | None | Undef
    _url: str | None | Undef
    _type: discord.ActivityType | None | Undef

    def __init__(self) -> None:
        self._used = False

        self._activity = undefined
        self._name = undefined
        self._url = undefined
        self._type = undefined

    def __del__(self) -> None:
        if not self._used:
            import warnings
            warnings.warn("VerifyActivity dropped without being used, did you forget an `assert`?", RuntimeWarning)

    def __bool__(self) -> bool:
        self._used = True

        bot_act = get_config().guilds[0].me.activity

        if self._activity is not undefined:
            return activity_eq(self._activity, bot_act)

        if bot_act is None:
            return (self._name not in [undefined, None]
                    and self._url not in [undefined, None]
                    and self._type not in [undefined, None])

        if isinstance(bot_act, discord.Game):
            pass
        elif isinstance(bot_act, discord.CustomActivity):
            pass
        elif isinstance(bot_act, discord.Spotify):
            pass
        else:
            if self._name is not undefined and self._name != bot_act.name:
                return False
            if self._url is not undefined and self._url != bot_act.url:
                return False
            if self._type is not undefined and self._type != bot_act.type:
                return False

        return True

    def matches(self, activity: discord.activity.ActivityTypes | None) -> 'VerifyActivity':
        """
            Ensure that the bot activity exactly matches the passed activity. Most restrictive possible check.

        :param activity: Activity to compare against
        :return: Self for chaining
        """
        if self._name is not undefined or self._url is not undefined or self._type is not undefined:
            raise ValueError("Verify exact match conflicts with verifying attributes")
        self._activity = activity
        return self

    def name(self, name: str | None) -> 'VerifyActivity':
        """
            Check that the activity name matches the input

        :param name: Name to match against
        :return: Self for chaining
        """
        if self._activity is not undefined:
            raise ValueError("Verify name conflicts with verifying exact match")
        self._name = name
        return self

    def url(self, url: str | None) -> 'VerifyActivity':
        """
            Check the the activity url matches the input

        :param url: Url to match against
        :return: Self for chaining
        """
        if self._activity is not undefined:
            raise ValueError("Verify url conflicts with verifying exact match")
        self._url = url
        return self

    def type(self, type: discord.ActivityType | None) -> 'VerifyActivity':
        """
            Check the activity type matches the input

        :param type: Type to match against
        :return: Self for chaining
        """
        if self._activity is not undefined:
            raise ValueError("Verify type conflicts with verifying exact match")
        self._type = type
        return self


class Verify:
    """
        Base for all kinds of verification builders. Used as an
        intermediate step for the return of verify().
    """

    def __init__(self) -> None:
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
