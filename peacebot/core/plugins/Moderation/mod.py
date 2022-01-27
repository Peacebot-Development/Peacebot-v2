from datetime import datetime, timedelta, timezone
from operator import mod
from time import time

import hikari
import lightbulb

from peacebot.core.utils.embed_colors import EmbedColors
from peacebot.core.utils.errors import ModerationError
from peacebot.core.utils.helper_functions import convert_time
from peacebot.core.utils.permissions import moderation_role_check

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
    now = datetime.now(timezone.utc)
    time_seconds = convert_time(ctx.options.time)
    then = now + timedelta(seconds=time_seconds)
    if (then - now).days > 28:
        raise ModerationError("You cannot timeout members for more than 28 days!")
    await member.edit(communication_disabled_until=then, reason=ctx.options.reason)
    embed = (
        hikari.Embed(
            description=f"🔇Timed Out -> {member}\n**Reason:** {ctx.options.reason}",
            color=EmbedColors.ERROR,
            timestamp=datetime.now().astimezone(),
        )
        .set_author(
            name=f"{ctx.author}(ID {ctx.author.id})", icon=ctx.author.avatar_url
        )
        .set_footer(text=f"Time: {ctx.options.time}")
        .set_thumbnail(member.avatar_url)
    )
    await ctx.respond(embed=embed)


@timeout.child
@lightbulb.option("reason", "Reason to remove timeout")
@lightbulb.option("member", "Member to remove timeout from", type=hikari.Member)
@lightbulb.command("disable", "Remove timeout from a member")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def disable_timeout_command(ctx: lightbulb.Context) -> None:
    member: hikari.Member = ctx.options.member
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
    await ctx.respond(embed=embed)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(mod_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(mod_plugin)
