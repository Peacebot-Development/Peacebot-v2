import logging
import math
import re

import hikari
import lightbulb

from peacebot.core.utils.embed_colors import EmbedColors

logger = logging.getLogger("error_handler")


class HelpersError(lightbulb.LightbulbError):
    pass


class ModerationError(lightbulb.LightbulbError):
    pass
