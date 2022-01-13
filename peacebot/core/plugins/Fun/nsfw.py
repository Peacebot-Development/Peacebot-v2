import random

import hikari
import lightbulb
from lightbulb import commands, context

from . import RedditCacher

nsfw_plugin = lightbulb.Plugin("NSFW")
nsfw_plugin.add_checks(
    lightbulb.bot_has_guild_permissions(
        hikari.Permissions.VIEW_CHANNEL
        | hikari.Permissions.SEND_MESSAGES
        | hikari.Permissions.EMBED_LINKS
    ),
    lightbulb.nsfw_channel_only,
)
reddit_cacher = RedditCacher("peacebot/cache/reddit.pickle")


async def send_random_post(ctx: context.Context, subreddit_name: str) -> None:
    posts = await reddit_cacher.get_subreddit_posts(subreddit_name)
    if not posts:
        raise lightbulb.LightbulbError("Internal Error Occured, please report!")

    post = random.choice(posts)
    embed = (
        hikari.Embed(
            title=post.title,
            url=post.url,
            color=hikari.Color.from_rgb(255, 255, 255),
        )
        .set_image(post.url)
        .set_footer(f"Why so horni?")
    )
    await ctx.respond(embed=embed)


@nsfw_plugin.command()
@lightbulb.command("ass", "Get some juicy ass pics", auto_defer=True)
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
@reddit_cacher.command("ass")
async def nsfw_ass(ctx: context.Context) -> None:
    await send_random_post(ctx, "ass")


@nsfw_plugin.command()
@lightbulb.command("boobs", "Get some juicy ass pics", auto_defer=True)
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
@reddit_cacher.command("boobs")
async def nsfw_boobs(ctx: context.Context) -> None:
    await send_random_post(ctx, "boobs")


@nsfw_plugin.command()
@lightbulb.command("pussy", "Get some juicy ass pics", auto_defer=True)
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
@reddit_cacher.command("pussy")
async def nsfw_pussy(ctx: context.Context) -> None:
    await send_random_post(ctx, "pussy")


@nsfw_plugin.command()
@lightbulb.command("hentai", "Get some juicy ass pics", auto_defer=True)
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
@reddit_cacher.command("hentai")
async def nsfw_hentai(ctx: context.Context) -> None:
    await send_random_post(ctx, "hentai")


@nsfw_plugin.command()
@lightbulb.command("cum", "Get some juicy ass pics", auto_defer=True)
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
@reddit_cacher.command("cumsluts")
async def nsfw_cum(ctx: context.Context) -> None:
    await send_random_post(ctx, "cumsluts")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(nsfw_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(nsfw_plugin)
