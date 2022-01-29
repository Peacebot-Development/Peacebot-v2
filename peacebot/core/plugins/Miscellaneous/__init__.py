import lightbulb
from apscheduler.schedulers.asyncio import AsyncIOScheduler


def fetch_scheduler(ctx: lightbulb.Context) -> AsyncIOScheduler:
    return ctx.bot.scheduler


async def send_remainder(ctx: lightbulb.Context, text: str) -> None:
    await ctx.respond(
        f"{ctx.author.mention} Remainder: `{text}`",
        user_mentions=True,
    )
