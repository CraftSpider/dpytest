
__title__ = "dpytest"
__author__ = "Rune Tynan"
__license__ = "MIT"
__copyright__ = "Copyright 2018-2019 CraftSpider"
__version__ = "0.0.15"

from . import backend
from .runner import *
from .enhance import embed_eq, embed_proxy_eq

import discord

discord.Embed.__eq__ = embed_eq
discord.embeds.EmbedProxy.__eq__ = embed_proxy_eq
