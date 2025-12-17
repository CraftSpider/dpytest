"""
    Utility functions that don't have a place anywhere else. If it doesn't sound like it fits anywhere else,
    and it's small, it probably goes here.
"""

import asyncio
from typing import TypeVar

import discord


def embed_eq(embed1: discord.Embed | None, embed2: discord.Embed | None) -> bool:
    if embed1 is None or embed2 is None:
        return embed1 == embed2

    return all([embed1.title == embed2.title,
                embed1.description == embed2.description,
                embed1.url == embed2.url,
                embed1.footer.text == embed2.footer.text,
                embed1.image.url == embed2.image.url,
                embed1.fields == embed2.fields])


def activity_eq(act1: discord.activity.ActivityTypes | None, act2: discord.activity.ActivityTypes | None) -> bool:
    if act1 is None or act2 is None:
        return act1 == act2

    match (act1, act2):
        case (discord.Activity, discord.Activity):
            return all([
                act1.name == act2.name,
                act1.url == act2.url,
                act1.type == act2.type,
                act1.details == act2.details,
                act1.emoji == act2.emoji,
            ])
        case (discord.Game, discord.Game):
            return all([
                act1.name == act2.name,
                act1.platform == act2.platform,
                act1.assets == act2.assets,
            ])
        case (discord.CustomActivity, discord.CustomActivity):
            return all([
                act1.name == act2.name,
                act1.emoji == act2.emoji,
            ])
        case (discord.Streaming, discord.Streaming):
            return all([
                act1.platform == act2.platform,
                act1.name == act2.name,
                act1.details == act2.details,
                act1.game == act2.game,
                act1.url == act2.url,
                act1.assets == act2.assets,
            ])
        case (discord.Spotify, discord.Spotify):
            return all([
                act1.title == act2.title,
                act1.artist == act2.artist,
                act1.album == act2.album,
                act1.album_cover_url == act2.album_cover_url,
                act1.track_id == act2.track_id,
                act1.start == act2.start,
                act1.end == act2.end,
            ])
    return False


def embed_proxy_eq(embed_proxy1: discord.embeds.EmbedProxy, embed_proxy2: discord.embeds.EmbedProxy) -> bool:
    return embed_proxy1.__repr__ == embed_proxy2.__repr__


T = TypeVar('T')

class PeekableQueue(asyncio.Queue[T]):
    """
        An extension of an asyncio queue with a peek message, so other code doesn't need to rely on unstable
        internal artifacts
    """

    def peek(self) -> T:
        """
            Peek the current last value in the queue, or raise an exception if there are no values

        :return: Last value in the queue, assuming there are any
        """
        return self._queue[-1]  # type: ignore[attr-defined]
