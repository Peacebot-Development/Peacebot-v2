import hikari
import lightbulb
from apscheduler.schedulers.asyncio import AsyncIOScheduler


def fetch_scheduler(ctx: lightbulb.context.Context) -> AsyncIOScheduler:
    return ctx.bot.d.scheduler


async def send_remainder(ctx: lightbulb.context.Context, text: str) -> None:
    await ctx.respond(
        f"{ctx.author.mention} Remainder: `{text}`",
        user_mentions=True,
    )
