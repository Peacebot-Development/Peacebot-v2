from datetime import datetime

import hikari
import lightbulb

from models import GuildModel, ModerationRoles
from peacebot.core.utils.embed_colors import EmbedColors
from peacebot.core.utils.permissions import PermissionsError

mod_helper = lightbulb.Plugin(
    "Moderation Helper",
    "Helper Commands that assist in running of moderation commands.",
)
mod_helper.add_checks(
    lightbulb.has_guild_permissions(
        perm1=hikari.Permissions.MANAGE_GUILD,
    )
)


@mod_helper.command
@lightbulb.command("config", "Setup Moderation roles for the server")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def config_command(ctx: lightbulb.Context) -> None:
    await ctx.bot.help_command.send_group_help(ctx, ctx.command)


@config_command.child
@lightbulb.option(
    "role", "The role to set as general moderation role", type=hikari.Role
)
@lightbulb.command(
    "moderation",
    "Setup General moderation role for the server[Example: /role moderation @Staff]",
)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def moderation_role_command(ctx: lightbulb.Context) -> None:
    role: hikari.Role = ctx.options.role
    model = await ModerationRoles.get_or_none(guild_id=ctx.guild_id)
    if model is None:
        await ModerationRoles.create(guild_id=ctx.guild_id, moderation_role=role.id)
    else:
        model.moderation_role = role.id
        await model.save()

    await ctx.respond(
        embed=hikari.Embed(
            title=f"Moderation Role - {ctx.get_guild().name}",
            description=f"General Moderation role was set to {role.mention}",
            color=EmbedColors.SUCCESS,
            timestamp=datetime.now().astimezone(),
        ),
        flags=hikari.MessageFlag.EPHEMERAL,
    )


@config_command.child
@lightbulb.option("role", "The role to set as mod role", type=hikari.Role)
@lightbulb.command(
    "mod", "Setup Mod role for the server[Example: /role mod @Moderator]"
)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def mod_role_command(ctx: lightbulb.Context) -> None:
    role: hikari.Role = ctx.options.role
    model = await ModerationRoles.get_or_none(guild_id=ctx.guild_id)
    if model is None:
        await ModerationRoles.create(guild_id=ctx.guild_id, mod_role=role.id)
    else:
        model.mod_role = role.id
        await model.save()
    await ctx.respond(
        embed=hikari.Embed(
            title=f"Mod Role - {ctx.get_guild().name}",
            description=f"Moderation role was set to {role.mention}",
            color=EmbedColors.SUCCESS,
            timestamp=datetime.now().astimezone(),
        ),
        flags=hikari.MessageFlag.EPHEMERAL,
    )


@config_command.child
@lightbulb.option("role", "The role to set as admin role", type=hikari.Role)
@lightbulb.command(
    "admin", "Setup Admin role for the server[Example: /role admin @Admin]"
)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def admin_role_command(ctx: lightbulb.Context) -> None:
    role: hikari.Role = ctx.options.role
    model = await ModerationRoles.get_or_none(guild_id=ctx.guild_id)
    if model is None:
        await ModerationRoles.create(guild_id=ctx.guild_id, admin_role=role.id)
    else:
        model.admin_role = role.id
        await model.save()
    await ctx.respond(
        embed=hikari.Embed(
            title=f"Admin Role - {ctx.get_guild().name}",
            description=f"Admin role was set to {role.mention}",
            color=EmbedColors.SUCCESS,
            timestamp=datetime.now().astimezone(),
        ),
        flags=hikari.MessageFlag.EPHEMERAL,
    )


@config_command.child
@lightbulb.command("list", "List all the moderation roles")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def list_command(ctx: lightbulb.Context) -> None:
    model = await ModerationRoles.get_or_none(guild_id=ctx.guild_id)
    if model is None:
        await ctx.bot.help_command.send_group_help(ctx, ctx.command)
        raise PermissionsError("No Moderation roles have been setup for the server!")

    embed = (
        hikari.Embed(
            title=f"Moderation Roles - {ctx.get_guild().name}",
            description="",
            color=EmbedColors.SUCCESS,
            timestamp=datetime.now().astimezone(),
        )
        .add_field(
            name="General Moderation Role",
            value=f"<@&{model.moderation_role}>" if model.moderation_role else "None",
            inline=True,
        )
        .add_field(
            name="Mod Role",
            value=f"<@&{model.mod_role}>" if model.mod_role else "None",
            inline=True,
        )
        .add_field(
            name="Admin Role",
            value=f"<@&{model.admin_role}>" if model.admin_role else "None",
            inline=True,
        )
    )
    await ctx.respond(embed=embed)


@config_command.child
@lightbulb.command("clear", "Clear all the moderation roles")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def clear_command(ctx: lightbulb.Context) -> None:
    model = await ModerationRoles.get_or_none(guild_id=ctx.guild_id)
    if model is None:
        await ctx.bot.help_command.send_group_help(ctx, ctx.command)
        raise PermissionsError("No Moderation roles have been setup for the server!")

    await model.delete()
    await ctx.respond(
        embed=hikari.Embed(
            title=f"Moderation Roles - {ctx.get_guild().name}",
            description="All moderation roles have been cleared",
            color=EmbedColors.SUCCESS,
            timestamp=datetime.now().astimezone(),
        )
    )


@config_command.child
@lightbulb.option(
    "channel", "The channel to set as mod-logs channel", type=hikari.GuildChannel
)
@lightbulb.command("modlog", "Set mod-logs for the server")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def modlog_command(ctx: lightbulb.Context) -> None:
    channel: hikari.GuildTextChannel = ctx.options.channel
    model = await GuildModel.get_or_none(id=ctx.guild_id)
    if model is None:
        raise PermissionsError("Guild Model not found for the server.")
    model.mod_log_channel = channel.id
    await model.save()
    await ctx.respond(
        embed=hikari.Embed(
            title=f"Config [Mod Log] - {ctx.get_guild().name}",
            description=f"<#{channel.id}> set to Mod Logs channel for the guild!",
            color=EmbedColors.SUCCESS,
            timestamp=datetime.now().astimezone(),
        )
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(mod_helper)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(mod_helper)
