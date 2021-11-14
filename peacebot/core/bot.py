from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import hikari
import lavasnek_rs
import lightbulb
import sake
import yuyo
from lightbulb.utils.data_store import DataStore
from tortoise import Tortoise

from models import GuildModel
from peacebot import bot_config, lavalink_config
from peacebot.core.event_handler import EventHandler
from peacebot.core.utils.activity import CustomActivity
from peacebot.core.utils.errors import on_error
from tortoise_config import tortoise_config

logger = logging.getLogger("peacebot.main")

HIKARI_VOICE = False


class Data:
    def __init__(self) -> None:
        self.lavalink: lavasnek_rs.Lavalink | None = None


class Peacebot(lightbulb.BotApp):
    """Custom class for initiating Lightbulb's BotApp"""

    def __init__(self) -> None:
        super().__init__(
            token=bot_config.token,
            prefix=lightbulb.when_mentioned_or(self.determine_prefix),
            default_enabled_guilds=bot_config.test_guilds,
            intents=hikari.Intents.ALL,
        )
        self.d = DataStore(
            data=Data(),
            component_client=yuyo.ComponentClient.from_gateway_bot(self),
            redis_cache=sake.RedisCache(self, self, address="redis://redis"),
        )
        self.custom_activity = CustomActivity(self)

    async def determine_prefix(self, _, message: hikari.Message) -> str:
        if not message.guild_id:
            return bot_config.prefix

        data, _ = await GuildModel.get_or_create(id=message.guild_id)
        return str(data.prefix)

    def run(self) -> None:
        self.event_manager.subscribe(hikari.StartingEvent, self.on_starting)
        self.event_manager.subscribe(hikari.StartedEvent, self.on_started)
        self.event_manager.subscribe(hikari.StoppingEvent, self.on_stopping)
        self.event_manager.subscribe(hikari.StoppedEvent, self.on_stopped)
        self.event_manager.subscribe(lightbulb.CommandErrorEvent, on_error)
        self.event_manager.subscribe(hikari.ShardReadyEvent, self.on_shard_ready)

        super().run(asyncio_debug=True)

    async def on_starting(self, _: hikari.StartingEvent) -> None:
        path = Path("./peacebot/core/plugins")
        for ext in path.glob(("**/") + "[!_]*.py"):
            self.load_extensions(".".join([*ext.parts[:-1], ext.stem]))
        logger.info("Connecting to Redis Cache....")
        await self.d.redis_cache.open()
        logger.info("Connected to Redis Cache.")
        asyncio.create_task(self.connect_db())

    async def on_shard_ready(self, _: hikari.ShardReadyEvent) -> None:
        builder = (
            lavasnek_rs.LavalinkBuilder(self.get_me(), bot_config.token)
            .set_host("lavalink")
            .set_password(lavalink_config.password)
        )
        if HIKARI_VOICE:
            builder.set_start_gateway(False)

        event_handler = EventHandler(self)
        lava_client = await builder.build(event_handler)
        self.d.data.lavalink = lava_client

    async def on_started(self, _: hikari.StartedEvent) -> None:
        asyncio.create_task(self.custom_activity.change_status())
        logger.info("Bot has started.")

    async def on_stopping(self, _: hikari.StoppingEvent) -> None:
        await self.d.component_client.close()

    async def on_stopped(self, _: hikari.StoppedEvent) -> None:
        await self.d.redis_cache.close()
        logger.info("Disconnected from Redis Cache.")

    async def connect_db(self) -> None:
        logger.info("Connecting to Database....")
        await Tortoise.init(tortoise_config)
        logger.info("Connected to DB sucessfully!")
