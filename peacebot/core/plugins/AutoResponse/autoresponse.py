from __future__ import annotations

import logging
import time

import hikari
import lightbulb
from lightbulb import commands, context

import peacebot.core.utils.helper_functions as hf
from models import AutoResponseModel, GuildModel
from peacebot.core.utils.embed_colors import EmbedColors

from . import AutoResponseError, clone_autoresponse, handle_message, is_valid_uuid

autoresponse_plugin = lightbulb.Plugin("AutoResponse")
autoresponse_plugin.add_checks(
    lightbulb.has_guild_permissions(
        hikari.Permissions.SEND_MESSAGES | hikari.Permissions.READ_MESSAGE_HISTORY
    ),
    lightbulb.human_only,
    lightbulb.bot_has_channel_permissions(
        hikari.Permissions.SEND_MESSAGES
        | hikari.Permissions.READ_MESSAGE_HISTORY
        | hikari.Permissions.EMBED_LINKS
    ),
)

logger = logging.getLogger(__name__)


@autoresponse_plugin.command
@lightbulb.command(
    "autoresponse",
    "Configure autoresponses for the current server",
    aliases=("ar", "autorsp"),
)
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
            title="Autoresponses",
            description="All the autoresponses in the guild",
            color=EmbedColors.GENERIC,
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
@lightbulb.option(
    "mentions",
    "If the response should mention the role/ user/ everyone or not",
    bool,
    default=False,
)
@lightbulb.option("response", "The response to send when trigger is pressed")
@lightbulb.option("trigger", "The trigger which will trigger the autoresponse")
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
        mentions=ctx.options.mentions or False,
    )

    await ctx.respond(
        f"**New Autoresponse** `{ctx.options.trigger}` has been added to the server."
    )


@autoresponse.child
@lightbulb.option("trigger", "Trigger of the autoresponse to remove")
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_GUILD))
@lightbulb.command(
    "remove",
    "Removes the provided autoresponse from the server",
    aliases=("del", "delete"),
)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def autoresponse_remove(ctx: context.Context) -> None:
    trigger: str = ctx.options.trigger
    autoresponse_model = await AutoResponseModel.get_or_none(
        guild__id=ctx.guild_id, trigger__iexact=trigger
    )
    if not autoresponse_model:
        raise AutoResponseError(
            f"`{trigger}` is not a valid autoresponse in this server or, may have already been deleted!"
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
            f"`{ctx.options.trigger}` is not a valid autoresponse in this server or, may have already been deleted!"
        )

    embed = (
        hikari.Embed(
            title="AutoResponse Info",
            description=f"Info about `{ctx.options.trigger}`",
            color=EmbedColors.GENERIC,
        )
        .add_field(name="ID:", value=autoresponse.id, inline=False)
        .add_field(name="Trigger:", value=autoresponse.trigger, inline=False)
        .add_field(name="Response:", value=autoresponse.response, inline=False)
        .add_field(
            name="Accepts Extra Text:",
            value=autoresponse.extra_text,
            inline=False,
        )
        .add_field(name="Mentions:", value=autoresponse.mentions, inline=False)
        .add_field(
            name="Allowed Channel:",
            value=autoresponse.allowed_channel or "Allowed in every channel",
            inline=False,
        )
        .add_field(name="Enabled:", value=autoresponse.enabled, inline=False)
        .add_field(
            name="Created By:", value=f"<@{autoresponse.created_by}>", inline=False
        )
        .add_field(
            name="Created At:",
            value=f"<t:{int(time.mktime(autoresponse.created_at.timetuple()))}:F>"
            or "No Data",
            inline=False,
        )
        .add_field(
            name="Updated At:",
            value=f"<t:{int(time.mktime(autoresponse.updated_at.timetuple()))}:F>"
            or "No Data",
            inline=False,
        )
    )
    await ctx.respond(embed=embed)


@autoresponse.child
@lightbulb.option(
    "trigger", "Trigger of the autoresponse you want to export", required=False
)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_GUILD))
@lightbulb.command("export", "Export autoresponse(s) to another server")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def autoresponse_export(ctx: context.Context) -> None:
    if not ctx.options.trigger:
        return await ctx.respond(
            f"You can import all the **autoresponses in this guild** using this id: ```{ctx.guild_id}```"
        )

    autoresponse_model = await AutoResponseModel.get_or_none(
        guild__id=ctx.guild_id, trigger=ctx.options.trigger.lower()
    )
    if not autoresponse_model:
        raise AutoResponseError(
            "Autoresponse with the provided trigger does not exist in this server."
        )

    await ctx.respond(
        f"You can **import autoresponse **`{ctx.options.trigger}` with this id: ```{autoresponse_model.id}```"
    )


@autoresponse.child
@lightbulb.option("id", "Id of the autoresponse(s)", str)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_GUILD))
@lightbulb.command("import", "Import autoreponse(s) from another server")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
@hf.error_handler()
async def autoresponse_import(ctx: context.Context) -> None:
    _id: str = ctx.options.id
    if _id == str(ctx.guild_id):
        raise AutoResponseError(
            "Please note that you **CANNOT** import autoresponse from the **Same Server**"
        )

    guild_model = await GuildModel.get_or_none(id=ctx.guild_id)

    if is_valid_uuid(_id):
        autoresponse_model = await AutoResponseModel.get_or_none(id=_id)
        if not autoresponse_model:
            raise AutoResponseError("Autoresponse with the provided id does not exist")

        new_model = clone_autoresponse(autoresponse_model, guild_model)
        await new_model.save()

        return await ctx.respond(
            f"**Autoresponse** `{autoresponse_model.trigger}` has been imported to this server."
        )

    elif _id.isdecimal():
        autoresponse_models = await AutoResponseModel.filter(guild_id=_id)
        if not autoresponse_models:
            raise AutoResponseError(
                "There were no autoresponses for the provided sever id"
            )

        server_autoresponses = await AutoResponseModel.filter(
            guild_id=ctx.guild_id
        ).only("trigger")

        autoresponse_models = filter(
            (lambda x: x.trigger not in [x.trigger for x in server_autoresponses]),
            autoresponse_models,
        )

        autoresponse_models = [
            clone_autoresponse(model, guild_model) for model in autoresponse_models
        ]
        await AutoResponseModel.bulk_create(autoresponse_models)
        return await ctx.respond(
            "AutoResponse(s) have been **imported** from the provided server."
        )

    raise AutoResponseError("Invalid import ID provided!")


@autoresponse.child
@lightbulb.option(
    "bool", "Either to enable or disable the autoresponse", bool, required=False
)
@lightbulb.option("trigger", "Trigger of the autoresponse to toggle")
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_GUILD))
@lightbulb.command("toggle", "Enable or disable the autoresponse", aliases=["tgl"])
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
@hf.error_handler()
async def autoresponse_toggle(ctx: context.Context) -> None:
    autoresponse = await AutoResponseModel.get_or_none(
        guild__id=ctx.guild_id, trigger__iexact=ctx.options.trigger
    )
    if not autoresponse:
        raise AutoResponseError(
            f"`{ctx.options.trigger}` is not a valid autoresponse in this server or, may have already been deleted!"
        )

    autoresponse.enabled = ctx.options.bool or not autoresponse.enabled
    await autoresponse.save()

    await ctx.respond(
        f"**Autoresponse** `{autoresponse.trigger}` has been **{'enabled' if autoresponse.enabled else 'disabled'}**."
    )


@autoresponse_plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message(event: hikari.GuildMessageCreateEvent) -> None:
    if not event.is_human or not event.message.content:
        return

    autoresponse_model = await handle_message(event.message)
    if not autoresponse_model:
        return

    channel = event.get_channel()
    await channel.send(
        autoresponse_model.response,
        user_mentions=autoresponse_model.mentions,
        role_mentions=autoresponse_model.mentions,
        mentions_everyone=autoresponse_model.mentions,
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(autoresponse_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(autoresponse_plugin)
