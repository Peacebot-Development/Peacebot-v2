from datetime import datetime, timedelta, timezone

import hikari
import lightbulb
from miru.ext import nav

from models import ModLogs
from peacebot.core.utils.embed_colors import EmbedColors
from peacebot.core.utils.errors import ModerationError
from peacebot.core.utils.helper_functions import convert_time
from peacebot.core.utils.permissions import (
    higher_role_check,
    mod_logs_check,
    mod_role_check,
    moderation_role_check,
    register_cases,
)
from peacebot.core.utils.utilities import _chunk

mod_plugin = lightbulb.Plugin("Mod", "Commands to be used by the Moderators")


@mod_plugin.command
@lightbulb.command("timeout", "Group that consists of the timeout commands")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
@moderation_role_check
async def timeout(ctx: lightbulb.Context) -> None:
    await ctx.bot.help_command.send_group_help(ctx, ctx.command)


@timeout.child
@lightbulb.option("reason", "Reason for the timeout", type=str)
@lightbulb.option("time", "The duration of timeout (Eg. 10s, 3d, 5d)", type=str)
@lightbulb.option("member", "The member to timeout", type=hikari.Member)
@lightbulb.command("enable", "Timeout a member from the server")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
@moderation_role_check
async def timeout_enable_command(ctx: lightbulb.Context) -> None:
    member: hikari.Member = ctx.options.member
    higher_role_check(ctx.member, member)
    mod_logs = await mod_logs_check(ctx)
    now = datetime.now(timezone.utc)
    time_seconds = convert_time(ctx.options.time)
    then = now + timedelta(seconds=time_seconds)
    if (then - now).days > 28:
        raise ModerationError("You cannot timeout members for more than 28 days!")
    await member.edit(communication_disabled_until=then, reason=ctx.options.reason)
    embed = (
        hikari.Embed(
            description=f"🔇Timed Out -> {member}\n**Reason:** {ctx.options.reason}",
            color=EmbedColors.INFO,
            timestamp=datetime.now().astimezone(),
        )
        .set_author(
            name=f"{ctx.author}(ID {ctx.author.id})", icon=ctx.author.avatar_url
        )
        .set_footer(text=f"Time: {ctx.options.time}")
        .set_thumbnail(member.avatar_url)
    )
    await mod_logs.send(embed=embed)
    response = await ctx.respond(embed=embed)
    message_link = (await response.message()).make_link(ctx.guild_id)
    await register_cases(
        guild_id=ctx.guild_id,
        moderator=ctx.author.id,
        target=member.id,
        reason=ctx.options.reason,
        message_link=message_link,
        channel_id=ctx.channel_id,
        type="TimeOut Enable",
    )


@timeout.child
@lightbulb.option("reason", "Reason to remove timeout")
@lightbulb.option("member", "Member to remove timeout from", type=hikari.Member)
@lightbulb.command("disable", "Remove timeout from a member")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def disable_timeout_command(ctx: lightbulb.Context) -> None:
    member: hikari.InteractionMember = ctx.options.member
    higher_role_check(ctx.member, member)
    mod_logs = await mod_logs_check(ctx)
    now = datetime.now(timezone.utc)
    await member.edit(communication_disabled_until=now, reason=ctx.options.reason)
    embed = (
        hikari.Embed(
            description=f"🔊 Removed TimeOut -> {member}\n**Reason:** {ctx.options.reason}",
            color=EmbedColors.SUCCESS,
            timestamp=datetime.now().astimezone(),
        )
        .set_author(
            name=f"{ctx.author}(ID {ctx.author.id})", icon=ctx.author.avatar_url
        )
        .set_thumbnail(member.avatar_url)
    )
    await mod_logs.send(embed=embed)
    response = await ctx.respond(embed=embed)
    message_link = (await response.message()).make_link(ctx.guild_id)
    await register_cases(
        guild_id=ctx.guild_id,
        moderator=ctx.author.id,
        target=member.id,
        reason=ctx.options.reason,
        message_link=message_link,
        channel_id=ctx.channel_id,
        type="TimeOut Disable",
    )


@mod_plugin.command
@lightbulb.option("reason", "The reason to kick the member")
@lightbulb.option("member", "The member to kick", type=hikari.Member)
@lightbulb.command("kick", "Kick the member from the server")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
@mod_role_check
async def kick_command(ctx: lightbulb.Context) -> None:
    member: hikari.InteractionMember = ctx.options.member
    higher_role_check(ctx.member, member)
    mod_logs = await mod_logs_check(ctx)
    await member.kick(reason=ctx.options.reason)
    embed = (
        hikari.Embed(
            description=f"👢 Kicked -> {member}\n**Reason:** {ctx.options.reason}",
            color=EmbedColors.INFO,
            timestamp=datetime.now().astimezone(),
        )
        .set_author(
            name=f"{ctx.author}(ID {ctx.author.id})", icon=ctx.author.avatar_url
        )
        .set_thumbnail(member.avatar_url)
    )
    await mod_logs.send(embed=embed)
    response = await ctx.respond(embed=embed)
    message_link = (await response.message()).make_link(ctx.guild_id)
    await register_cases(
        guild_id=ctx.guild_id,
        moderator=ctx.author.id,
        target=member.id,
        reason=ctx.options.reason,
        message_link=message_link,
        channel_id=ctx.channel_id,
        type="Kick",
    )


@mod_plugin.command
@lightbulb.option(
    "days",
    "Specify number of days of messages to delete(Min - 0, Max- 7)",
    required=False,
    type=int,
)
@lightbulb.option("reason", "The reason to ban the member")
@lightbulb.option("member", "The member to ban", type=hikari.Member)
@lightbulb.command("ban", "Ban the member from the server")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
@mod_role_check
async def ban_command(ctx: lightbulb.Context) -> None:
    member: hikari.InteractionMember = ctx.options.member
    higher_role_check(ctx.member, member)
    mod_logs = await mod_logs_check(ctx)
    if ctx.options.days > 7:
        raise ModerationError("Cannot delete messages more than 7 days old!")
    await member.ban(
        delete_message_days=ctx.options.days or 0, reason=ctx.options.reason
    )
    embed = (
        hikari.Embed(
            description=f"🔨 Banned -> {member}\n**Reason:** {ctx.options.reason}",
            color=EmbedColors.ERROR,
            timestamp=datetime.now().astimezone(),
        )
        .set_author(
            name=f"{ctx.author}(ID {ctx.author.id})", icon=ctx.author.avatar_url
        )
        .set_thumbnail(member.avatar_url)
    )
    await mod_logs.send(embed=embed)
    response = await ctx.respond(embed=embed)
    message_link = (await response.message()).make_link(ctx.guild_id)
    await register_cases(
        guild_id=ctx.guild_id,
        moderator=ctx.author.id,
        target=member.id,
        reason=ctx.options.reason,
        message_link=message_link,
        channel_id=ctx.channel_id,
        type="Ban",
    )


@mod_plugin.command
@lightbulb.command("case", "Group for case commands")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def case_command(ctx: lightbulb.Context) -> None:
    await ctx.bot.help_command.send_group_help(ctx, ctx.command)


@case_command.child
@lightbulb.option("case_id", "Case ID to look for")
@lightbulb.command("search", "Get a specific case")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def case_search_command(ctx: lightbulb.Context) -> None:
    model = await ModLogs.get_or_none(guild_id=ctx.guild_id, id=ctx.options.case_id)
    if model is None:
        raise ModerationError("No case found with that ID.")
    embed = hikari.Embed(
        title=f"{model.type} Case | No. {model.id}",
        description=f"[Jump to Message!]({model.message})",
        color=EmbedColors.INFO,
    )
    fields: list[tuple[str, str | int, bool]] = [
        ("Moderator", model.moderator, True),
        ("Target", model.target, True),
        ("Reason", model.reason, True),
        ("Channel", model.channel, True),
        ("Guild ID", model.guild_id, True),
        (
            "Time of Action",
            f"<t:{int(model.timestamp.timestamp())}:F> • <t:{int(model.timestamp.timestamp())}:R>",
            False,
        ),
    ]
    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)

    await ctx.respond(embed=embed)


@case_command.child
@lightbulb.command("list", "List all the Moderation Cases")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
@moderation_role_check
async def case_list_command(ctx: lightbulb.Context) -> None:
    case_model = await ModLogs.filter(guild_id=ctx.guild_id)
    if not len(case_model):
        raise ModerationError("No Cases could be found for the guild!")

    cases = [
        "#{0} - <t:{1}:R> -> {2}\n**Type**: ```{3}```".format(
            model.id,
            int(model.timestamp.timestamp()),
            model.moderator,
            model.type,
        )
        for (_, model) in enumerate(case_model)
    ]
    fields = [
        hikari.Embed(
            title="List of Cases", description="\n".join(case), color=EmbedColors.INFO
        ).set_footer(text=f"Page: {index + 1}")
        for index, case in enumerate(_chunk(cases, 5))
    ]

    navigator = nav.NavigatorView(app=ctx.bot, pages=fields)
    await navigator.send(ctx.interaction or ctx.channel_id)
    await navigator.wait()


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(mod_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(mod_plugin)
