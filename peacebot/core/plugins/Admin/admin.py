import hikari
import lightbulb
from lightbulb import commands

from models import GuildModel

admin_plugin = lightbulb.Plugin(
    name="Admin", description="Admin commands for the server"
)
admin_plugin.add_checks(
    lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR)
)


@admin_plugin.command
@lightbulb.option("prefix", "Custom prefix for the server.")
@lightbulb.command("changeprefix", "Change the prefix for the server.", aliases=["chp"])
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def changeprefix(ctx: lightbulb.context.Context) -> None:
    prefix = ctx.options.prefix
    model = await GuildModel.get_or_none(id=ctx.guild_id)
    model.prefix = prefix
    await model.save()

    await ctx.respond(f"I set your guild's prefix to `{prefix}`")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(admin_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(admin_plugin)
