from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import aioredis
import hikari
import lavasnek_rs
import lightbulb
import yuyo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asyncpraw import Reddit
from lightbulb.utils.data_store import DataStore
from reddist import RedisRedditCacher
from tortoise import Tortoise

from models import GuildModel
from peacebot import bot_config, lavalink_config
from peacebot.config.reddit import reddit_config
from peacebot.core.event_handler import EventHandler
from peacebot.core.utils.activity import CustomActivity
from peacebot.core.utils.embed_colors import EmbedColors
from peacebot.core.utils.errors import on_error
from tortoise_config import tortoise_config

logger = logging.getLogger("peacebot.main")
logger.setLevel(logging.DEBUG)

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
        redis = aioredis.from_url(url="redis://redis")
        self.d = DataStore(
            data=Data(),
            component_client=yuyo.ComponentClient.from_gateway_bot(self),
            redis=redis,
            reddit_cacher=RedisRedditCacher(
                Reddit(
                    client_id=reddit_config.client_id,
                    client_secret=reddit_config.client_secret,
                    user_agent="Peace Bot",
                ),
                redis,
            ),
            scheduler=AsyncIOScheduler(),
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
        self.event_manager.subscribe(hikari.GuildMessageCreateEvent, self.on_message)

        super().run(asyncio_debug=True)

    async def on_starting(self, _: hikari.StartingEvent) -> None:
        path = Path("./peacebot/core/plugins")
        for ext in path.glob(("**/") + "[!_]*.py"):
            self.load_extensions(".".join([*ext.parts[:-1], ext.stem]))
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
        self.d.scheduler.start()
        asyncio.create_task(self.custom_activity.change_status())
        logger.info("Bot has started sucessfully.")

    async def on_stopping(self, _: hikari.StoppingEvent) -> None:
        self.d.scheduler.shutdown()
        logger.info("Bot is stopping...")

    async def on_stopped(self, _: hikari.StoppedEvent) -> None:
        logger.info("Bot has stopped sucessfully.")

    async def connect_db(self) -> None:
        logger.info("Connecting to Database....")
        await Tortoise.init(tortoise_config)
        logger.info("Connected to DB sucessfully!")

    async def on_message(self, event: hikari.GuildMessageCreateEvent) -> None:
        if not event.is_human or not event.message.content:
            return

        if not f"<@!{self.get_me().id}>" == event.message.content.strip():
            return
        model = await GuildModel.get_or_none(id=event.guild_id)
        prefix = model.prefix
        response = f"""
            Hi {event.author.mention}, My prefix here is {self.get_me().mention} or `{prefix}`
            Slash Commands are also here. Type in / and then select command from the popup
            You can view the help using `{prefix}help`
            Thank you for using me.
            """

        await event.message.respond(
            embed=hikari.Embed(description=response, color=EmbedColors.INFO).set_footer(
                text=f"Cheers from the Peacebot Team."
            )
        )
