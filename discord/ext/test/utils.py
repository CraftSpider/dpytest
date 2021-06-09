"""
    Utility functions that don't have a place anywhere else. If it doesn't sound like it fits anywhere else,
    and it's small, it probably goes here.
"""

import asyncio
import discord
import typing


def embed_eq(embed1: typing.Optional[discord.Embed], embed2: typing.Optional[discord.Embed]) -> bool:
    if embed1 == embed2:
        return True
    elif embed1 is None and embed2 is not None:
        return False
    elif embed2 is None and embed1 is not None:
        return False

    return all([embed1.title == embed2.title,
                embed1.description == embed2.description,
                embed1.url == embed2.url,
                embed1.footer.text == embed2.footer.text,
                embed1.image.url == embed2.image.url])


def activity_eq(act1: typing.Optional[discord.Activity], act2: typing.Optional[discord.Activity]) -> bool:
    if act1 == act2:
        return True
    elif act1 is None and act2 is not None:
        return False
    elif act2 is None and act1 is not None:
        return False

    return all([
        act1.name == act2.name,
        act1.url == act2.url,
        act1.type == act2.type,
        act1.details == act2.details,
        act1.emoji == act2.emoji,
    ])


def embed_proxy_eq(embed_proxy1, embed_proxy2):
    return embed_proxy1.__repr__ == embed_proxy2.__repr__


class PeekableQueue(asyncio.Queue):
    """
        An extension of an asyncio queue with a peek message, so other code doesn't need to rely on unstable
        internal artifacts
    """

    def peek(self):
        """
            Peek the current last value in the queue, or raise an exception if there are no values

        :return: Last value in the queue, assuming there are any
        """
        return self._queue[-1]
