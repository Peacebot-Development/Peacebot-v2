import logging

import hikari
import lightbulb
from lightbulb import commands

from peacebot.core.utils.embed_colors import EmbedColors

nsfw_plugin = lightbulb.Plugin("NSFW")
nsfw_plugin.add_checks(
    lightbulb.bot_has_guild_permissions(
        hikari.Permissions.VIEW_CHANNEL
        | hikari.Permissions.SEND_MESSAGES
        | hikari.Permissions.EMBED_LINKS
    ),
    lightbulb.nsfw_channel_only,
)


async def send_random_post(ctx: lightbulb.Context, subreddit_name: str) -> None:
    post = await ctx.bot.d.reddit_cacher.get_random_post(subreddit_name)
    if not post:
        raise lightbulb.LightbulbError("Internal Error Occured, please report!")
    logging.info(post)
    embed = (
        hikari.Embed(
            title=post.title,
            url="https://www.reddit.com" + post.permalink,
            color=EmbedColors.GENERIC,
        )
        .set_image(post.url)
        .set_footer(f"Why so horni?")
    )
    await ctx.respond(embed=embed)


@nsfw_plugin.command()
@lightbulb.command("ass", "Get some juicy ass pics", auto_defer=True)
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
async def nsfw_ass(ctx: lightbulb.Context) -> None:
    await send_random_post(ctx, "ass")


@nsfw_plugin.command()
@lightbulb.command("boobs", "Mommy milkers?", auto_defer=True)
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
async def nsfw_boobs(ctx: lightbulb.Context) -> None:
    await send_random_post(ctx, "boobs")


@nsfw_plugin.command()
@lightbulb.command("pussy", "pussy cat, meow", auto_defer=True)
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
async def nsfw_pussy(ctx: lightbulb.Context) -> None:
    await send_random_post(ctx, "pussy")


@nsfw_plugin.command()
@lightbulb.command("hentai", "no judging", auto_defer=True)
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
async def nsfw_hentai(ctx: lightbulb.Context) -> None:
    await send_random_post(ctx, "hentai")


@nsfw_plugin.command()
@lightbulb.command("cum", "fappacino", auto_defer=True)
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
async def nsfw_cum(ctx: lightbulb.Context) -> None:
    await send_random_post(ctx, "cumsluts")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(nsfw_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(nsfw_plugin)
