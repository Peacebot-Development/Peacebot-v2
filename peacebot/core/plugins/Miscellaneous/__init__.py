import lightbulb
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from peacebot.core.utils.time import TimeConverter


def fetch_scheduler(ctx: lightbulb.Context) -> AsyncIOScheduler:
    return ctx.bot.d.scheduler


async def convert_time(ctx: lightbulb.Context, time: str) -> float:
    seconds = await TimeConverter.convert(TimeConverter, ctx, time)

    return seconds


async def send_remainder(ctx: lightbulb.Context, text: str) -> None:
    await ctx.respond(
        f"{ctx.author.mention} Remainder: `{text}`",
        user_mentions=True,
    )
