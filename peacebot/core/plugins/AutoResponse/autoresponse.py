import logging

import hikari
import lightbulb
from lightbulb import commands, context

from models import AutoResponseModel

from . import AutoResponseError, handle_message

autoresponse_plugin = lightbulb.Plugin("AutoResponse")
autoresponse_plugin.add_checks(
    lightbulb.has_guild_permissions(
        hikari.Permissions.SEND_MESSAGES | hikari.Permissions.READ_MESSAGE_HISTORY
    ),
    lightbulb.human_only,
    lightbulb.bot_has_channel_permissions(
        hikari.Permissions.SEND_MESSAGES
        | hikari.Permissions.READ_MESSAGE_HISTORY
        | hikari.Permissions.EMBED_LINK
    ),
)

logger = logging.getLogger(__name__)


@autoresponse_plugin.command
@lightbulb.command("autoresponse", "Configure autoresponses for the current server")
@lightbulb.implements(commands.PrefixCommandGroup, commands.SlashCommandGroup)
async def autoresponse(ctx: context.Context) -> None:
    await ctx.bot.help_command.send_group_help(ctx, ctx.command)


@autoresponse.child
@lightbulb.command("list", "Get the list of all the autoresponses in the server")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def autoresponse_list(ctx: context.Context) -> None:
    autoresponses = await AutoResponseModel.filter(guild__id=ctx.guild_id)
    enabled_autoresponses = [
        f"`{autoresponse.trigger}`"
        for autoresponse in autoresponses
        if autoresponse.enabled
    ] or "There are no enabled autoresponses"
    disabled_autoresponses = [
        f"`{autoresponse.trigger}`"
        for autoresponse in autoresponses
        if not autoresponse.enabled
    ] or "There are no disabled autoresponses"

    embed = (
        hikari.Embed(
            title="Autoresponses", description="All the autoresponses in the guild"
        )
        .add_field(
            name="Enabled autoresponses",
            value=(", ".join(enabled_autoresponses))
            if isinstance(enabled_autoresponses, list)
            else enabled_autoresponses,
        )
        .add_field(
            name="Disabled Autoresponses",
            value=(
                ", ".join(disabled_autoresponses)
                if isinstance(disabled_autoresponses, list)
                else disabled_autoresponses
            ),
        )
    )
    await ctx.respond(embed=embed)


@autoresponse.child
@lightbulb.option(
    "allowed_channel",
    "The only channel where this specific autoresponse should be allowed",
    hikari.TextableGuildChannel,
    required=False,
)
@lightbulb.option(
    "extra_text",
    "If the autoresponse should invoke even when there is extra text along with the trigger",
    bool,
    required=False,
)
@lightbulb.option("response", "The response to send when trigger is pressed")
@lightbulb.option("trigger", "The trigger which will trigger the autoresponse")
@lightbulb.option("trigger", "Trigger of the autoresponse to remove")
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_GUILD))
@lightbulb.command("add", "Add a new autoresponse to the server")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def autoresponse_add(ctx: context.Context) -> None:
    if await AutoResponseModel.exists(
        guild__id=ctx.guild_id, trigger__iexact=ctx.options.trigger
    ):
        raise AutoResponseError(
            "Autoresponse with this trigger already exists, please delete other autoresponse to create new"
        )

    logger.info(ctx.guild_id)
    await AutoResponseModel.create(
        guild_id=ctx.guild_id,
        trigger=ctx.options.trigger.lower(),
        response=ctx.options.response,
        created_by=ctx.author.id,
        allowed_channel=ctx.options.allowed_channel,
        extra_text=ctx.options.extra_text or False,
    )

    await ctx.respond(
        f"**New Autoresponse** `{ctx.options.trigger}` has been added to the server."
    )


@autoresponse.child
@lightbulb.option("trigger", "Trigger of the autoresponse to remove")
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_GUILD))
@lightbulb.command("remove", "Removes the provided autoresponse from the server")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def autoresponse_remove(ctx: context.Context) -> None:
    trigger: str = ctx.options.trigger
    autoresponse_model = await AutoResponseModel.get_or_none(
        guild__id=ctx.guild_id, trigger__iexact=trigger
    )
    if not autoresponse_model:
        raise AutoResponseError(
            f"`{trigger}` is not a valid autoresponse in this guild or, may have already been deleted!"
        )

    await autoresponse_model.delete()
    await ctx.respond(f"**Autoresponse** `{trigger}` has been removed from the server.")


@autoresponse.child
@lightbulb.option("trigger", "Trigger of the autoresponse to get info on")
@lightbulb.command("info", "Get the info of the autoresponse")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def autoresponse_info(ctx: context.Context):
    autoresponse = await AutoResponseModel.get_or_none(
        guild__id=ctx.guild_id, trigger=ctx.options.trigger.lower()
    )
    if not autoresponse:
        raise AutoResponseError(
            f"`{ctx.options.trigger}` is not a valid autoresponse in this guild or, may have already been deleted!"
        )

    embed = (
        hikari.Embed(
            title="AutoResponse Info",
            description=f"Info about `{ctx.options.trigger}`",
        )
        .add_field(name="ID:", value=autoresponse.id, inline=False)
        .add_field(name="Trigger:", value=autoresponse.trigger, inline=False)
        .add_field(name="Response:", value=autoresponse.response, inline=False)
        .add_field(
            name="Accepts Extra Text:",
            value=autoresponse.extra_text,
            inline=False,
        )
        .add_field(
            name="Created By:", value=f"<@{autoresponse.created_by}>", inline=False
        )
    )

    await ctx.respond(embed=embed)


@autoresponse_plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message(event: hikari.GuildMessageCreateEvent) -> None:
    if not event.is_human or not event.message.content:
        return

    autoresponse_model = await handle_message(event.message)
    if not autoresponse_model:
        return

    channel = event.get_channel()
    await channel.send(autoresponse_model.response)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(autoresponse_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(autoresponse_plugin)
