
__title__ = "dpytest"
__author__ = "Rune Tynan"
__license__ = "MIT"
__copyright__ = "Copyright 2018-2019 CraftSpider"
__version__ = "0.6.7"

from . import backend as backend

from .runner import *

from .utils import embed_eq as embed_eq
from .utils import activity_eq as activity_eq
from .utils import embed_proxy_eq as embed_proxy_eq
from .utils import PeekableQueue as PeekableQueue

from .verify import verify as verify
from .verify import Verify as Verify
from .verify import VerifyMessage as VerifyMessage
from .verify import VerifyActivity as VerifyActivity
