import logging
from datetime import datetime
from typing import TYPE_CHECKING

import hikari
import lavasnek_rs
import miru

from peacebot.core.plugins.Music import MusicError, fetch_lavalink
from peacebot.core.plugins.Music.music import Controls
from peacebot.core.utils.embed_colors import EmbedColors

if TYPE_CHECKING:
    from .bot import Peacebot

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, bot: "Peacebot") -> None:
        self.bot = bot

    async def track_start(
        self, lavalink: lavasnek_rs.Lavalink, event: lavasnek_rs.TrackStart
    ) -> None:
        view = Controls(self.bot, timeout=120)
        logger.info(f"Track started on Guild: {event.guild_id}")
        node = await lavalink.get_guild_node(event.guild_id)

        if node:
            data = node.get_data()
            channel_id = data[event.guild_id]
            channel = self.bot.cache.get_guild_channel(channel_id)

        embed = (
            hikari.Embed(
                title="Now Playing",
                timestamp=datetime.now().astimezone(),
                description=f"[{node.now_playing.track.info.title}]({node.now_playing.track.info.uri})",
                color=EmbedColors.INFO,
            )
            .add_field(
                name="Requested By",
                value=f"<@{node.now_playing.requester}>",
                inline=True,
            )
            .add_field(
                name="Author", value=node.now_playing.track.info.author, inline=True
            )
        )

        message = await channel.send(embed=embed, components=view.build())
        view.start(message)
        await view.wait()

    async def track_finish(
        self, _: lavasnek_rs.Lavalink, event: lavasnek_rs.TrackFinish
    ):
        logger.info(f"Track finished on Guild: {event.guild_id}")

    async def track_exception(
        self, lavalink: lavasnek_rs.Lavalink, event: lavasnek_rs.TrackException
    ):
        logger.warning("Track Exception happened on Guild: %d", event.guild_id)

        skip = await lavalink.skip(event.guild_id)
        node = await lavalink.get_guild_node(event.guild_id)

        if not skip:
            raise MusicError("Nothing to Skip.")
        else:
            if not node.queue and not node.now_playing:
                await lavalink.stop(event.guild_id)

    async def track_stuck(
        self, lavalink: lavasnek_rs.Lavalink, event: lavasnek_rs.TrackStuck
    ) -> None:
        view = Controls(self.bot, timeout=120)
        logger.warning("Track stuck on Guild: %d", event.guild_id)
        node = await lavalink.get_guild_node(event.guild_id)
        if node:
            data = node.get_data()
            channel_id = data[event.guild_id]
            channel = self.bot.cache.get_guild_channel(channel_id)
        embed = hikari.Embed(
            title="Track Stuck",
            description=f"Looks like [{node.now_playing.track.info.title}]({node.now_playing.track.info.uri}) got stuck!",
            color=EmbedColors.ERROR,
        )
        message = await channel.send(embed=embed, components=view.build())
        view.start(message)
        await view.wait()
