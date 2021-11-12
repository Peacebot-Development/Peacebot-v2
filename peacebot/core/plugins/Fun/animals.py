import aiohttp
import hikari
import lightbulb
from lightbulb import commands

from peacebot.core.utils.buttons import create_source_button

animals_plugin = lightbulb.Plugin("Animals")
animals_plugin.add_checks(
    lightbulb.bot_has_guild_permissions(
        hikari.Permissions.VIEW_CHANNEL
        | hikari.Permissions.SEND_MESSAGES
        | hikari.Permissions.EMBED_LINKS
    ),
)


@animals_plugin.command
@lightbulb.add_cooldown(1, 5, lightbulb.UserBucket)
@lightbulb.command("dog", "Get a picture of a dog.")
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
async def dog(ctx: lightbulb.context.Context) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get("https://dog.ceo/api/breeds/image/random") as resp:
            data = await resp.json()

            image = data.get("message")

        embed = (
            hikari.Embed(title="Woof Woof!", color=0xD35400)
            .set_image(image)
            .set_footer(text=f"Requested by {ctx.author}")
        )
        button = create_source_button(ctx, "https://dog.ceo/")
        await ctx.respond(embed=embed, component=button)


@animals_plugin.command
@lightbulb.add_cooldown(1, 5, lightbulb.UserBucket)
@lightbulb.command("fox", "Get a picture of a fox")
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
async def cat(ctx: lightbulb.context.Context) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get("https://randomfox.ca/floof/") as r:
            data = await r.json()
            image = data.get("image")

    embed = (
        hikari.Embed(title="What does the fox say?", color=0xD35400)
        .set_image(image)
        .set_footer(text=f"Requested by {ctx.author}")
    )
    button = create_source_button(ctx, "https://randomfox.ca")

    await ctx.respond(embed=embed, component=button)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(animals_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(animals_plugin)
