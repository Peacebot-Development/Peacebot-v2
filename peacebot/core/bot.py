from __future__ import annotations

import asyncio
import logging
from typing import Sequence

import hikari
import lightbulb
import sake
from tortoise import Tortoise

from models import GuildModel
from peacebot import TEST_GUILD, bot_config
from peacebot.core.utils.activity import CustomActivity
from tortoise_config import tortoise_config

logger = logging.getLogger("peacebot.main")


class Peacebot(lightbulb.BotApp):
    """Custom class for initiating Lightbulb's BotApp"""

    def __init__(self) -> None:
        super().__init__(
            token=bot_config.token,
            prefix=lightbulb.when_mentioned_or(self.determine_prefix),
            default_enabled_guilds=TEST_GUILD,
            intents=hikari.Intents.ALL,
        )
        self.redis_cache = sake.RedisCache(self, self, address="redis://redis")
        self.custom_activity = CustomActivity(self)

    async def determine_prefix(self, bot, message: hikari.Message) -> str:
        if not message.guild_id:
            return bot_config.prefix

        data, _ = await GuildModel.get_or_create(id=message.guild_id)
        prefix = str(data.prefix)
        return prefix

    def run(self) -> None:
        self.event_manager.subscribe(hikari.StartingEvent, self.on_starting)
        self.event_manager.subscribe(hikari.StartedEvent, self.on_started)
        self.event_manager.subscribe(hikari.StoppingEvent, self.on_stopping)
        self.event_manager.subscribe(hikari.StoppedEvent, self.on_stopped)

        super().run(asyncio_debug=True)

    async def on_starting(self, event: hikari.StartingEvent) -> None:
        self.load_extensions_from("peacebot/core/plugins")
        logger.info("Connecting to Redis Cache....")
        await self.redis_cache.open()
        logger.info("Connected to Redis Cache.")
        asyncio.create_task(self.connect_db())

    async def on_started(self, event: hikari.StartedEvent) -> None:
        asyncio.create_task(self.custom_activity.change_status())
        logger.info("Bot has started.")

    async def on_stopping(self, event: hikari.StoppingEvent) -> None:
        ...

    async def on_stopped(self, event: hikari.StoppedEvent) -> None:
        await self.redis_cache.close()
        logger.info("Disconnected from Redis Cache.")

    async def connect_db(self) -> None:
        logger.info("Connecting to Database....")
        await Tortoise.init(tortoise_config)
        logger.info("Connected to DB sucessfully!")
