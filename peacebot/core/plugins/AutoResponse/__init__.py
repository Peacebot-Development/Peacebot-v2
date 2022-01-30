from __future__ import annotations

import uuid

import hikari
from lightbulb import LightbulbError
from tortoise.query_utils import Q

from models import AutoResponseModel, GuildModel


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


def is_valid_uuid(_uuid: str):
    try:
        uuid.UUID(str(_uuid), version=4)
        return True
    except ValueError:
        return False


def clone_autoresponse(
    previous_model: AutoResponseModel, guild_model: GuildModel
) -> AutoResponseModel:
    new_model = previous_model.clone()
    new_model.id = uuid.uuid4()
    new_model._custom_generated_pk = False
    new_model.guild = guild_model
    new_model.allowed_channel = None
    return new_model
