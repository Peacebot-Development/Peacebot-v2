import asyncio
from itertools import cycle
from typing import TYPE_CHECKING

import hikari

if TYPE_CHECKING:
    from peacebot.core.bot import Peacebot


class CustomActivity:
    """
    Custom class that changes the bot's activity
    """

    def __init__(self, bot: "Peacebot") -> None:
        self.bot = bot
        self._statuses = cycle(
            [
                hikari.Activity(
                    type=hikari.ActivityType.WATCHING, name="Slash Commands Poggers"
                ),
                hikari.Activity(type=hikari.ActivityType.WATCHING, name="Ihihihihi"),
            ]
        )

    async def change_status(self) -> None:
        """
        Function that changes the Bot's Status Every 1 minute
        """
        while True:
            new_presence = next(self._statuses)
            await self.bot.update_presence(
                activity=new_presence, status=hikari.Status.DO_NOT_DISTURB
            )
            await asyncio.sleep(60)
