from __future__ import annotations

import hikari
from lightbulb import LightbulbError
from tortoise.query_utils import Q

from models import AutoResponseModel


class AutoResponseError(LightbulbError):
    ...


async def handle_message(message: hikari.Message) -> AutoResponseModel | None:
    autoresponse_models = await AutoResponseModel.filter(
        Q(
            Q(
                trigger__in=map(lambda m: m.lower(), message.content.split()),
                extra_text=True,
            )
            | Q(trigger__iexact=message.content, extra_text=False)
        )
        & Q(Q(allowed_channel__isnull=True) | Q(allowed_channel=message.channel_id)),
        guild__id=message.guild_id,
        enabled=True,
    )
    return autoresponse_models[0] if autoresponse_models else None
