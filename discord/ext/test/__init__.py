
__title__ = "dpytest"
__author__ = "Rune Tynan"
__license__ = "MIT"
__copyright__ = "Copyright 2018-2019 CraftSpider"
__version__ = "0.6.0"

from . import backend
from .runner import *
from .utils import embed_eq, activity_eq, embed_proxy_eq, PeekableQueue
from .verify import verify, Verify, VerifyMessage, VerifyActivity
