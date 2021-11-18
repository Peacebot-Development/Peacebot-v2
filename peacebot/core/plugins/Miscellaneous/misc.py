from datetime import datetime, timedelta

import hikari
import lightbulb
from lightbulb import commands

import peacebot.core.utils.helper_functions as hf
from peacebot.core.utils.embed_colors import EmbedColors

from . import convert_time, fetch_scheduler, send_remainder

misc_plugin = lightbulb.Plugin("Misc", "Miscellaneous Commands for the Bot")


@misc_plugin.command
@lightbulb.add_cooldown(1, 5, lightbulb.UserBucket)
@lightbulb.option("member", "Get member", type=hikari.Member, required=False)
@lightbulb.command("avatar", "View a member's avatar", aliases=["av"])
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
@hf.error_handler()
async def avatar(ctx: lightbulb.context.Context) -> None:
    member: hikari.Member = ctx.options.member or ctx.member

    embed = (
        hikari.Embed(
            title=f"Avatar - {member}",
            color=EmbedColors.INFO,
            timestamp=datetime.now().astimezone(),
        )
        .set_image(member.avatar_url)
        .set_footer(f"Requested by {ctx.author}")
    )

    await ctx.respond(embed=embed)


@misc_plugin.command
@lightbulb.add_cooldown(1, 5, lightbulb.UserBucket)
@lightbulb.option("member", "Get member", type=hikari.Member, required=False)
@lightbulb.command("userinfo", "Get info of a user in a guild")
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
@hf.error_handler()
async def userinfo(ctx: lightbulb.context.Context) -> None:
    guild = ctx.get_guild()
    member: hikari.Member = ctx.options.member or ctx.member

    created_at = int(member.created_at.timestamp())
    joined_at = int(member.joined_at.timestamp())

    roles = (await member.fetch_roles())[1:]

    perms = hikari.Permissions.NONE

    for role in roles:
        perms |= role.permissions

    permissions = str(perms).split("|")

    status = (
        member.get_presence().visible_status if member.get_presence() else "Offline"
    )

    if member.id == guild.owner_id:
        acknowlegdement = "Server Owner"
    elif "ADMINISTRATOR" in permissions:
        acknowlegdement = "Administrator"
    elif "MANAGE_GUILD" in permissions:
        acknowlegdement = "Moderator"
    elif "MANAGE_MESSAGES" in permissions:
        acknowlegdement = "Staff"
    else:
        acknowlegdement = "Member"

    embed = (
        hikari.Embed(
            color=EmbedColors.INFO,
            timestamp=datetime.now().astimezone(),
            title=f"Userinfo of {member}",
        )
        .set_thumbnail(member.avatar_url)
        .set_footer(text=f"Requested by {ctx.author}", icon=ctx.author.avatar_url)
    )

    fields = [
        ("ID", member.id, True),
        ("Joined", f"<t:{joined_at}:F> • <t:{joined_at}:R>", True),
        ("Created", f"<t:{created_at}:F> • <t:{created_at}:R>", True),
        ("Status", status.title(), True),
        ("Acknowledgement", acknowlegdement, True),
        ("Is Bot", member.is_bot, True),
        (
            "Permissions",
            ", ".join(perm.replace("_", " ").title() for perm in permissions),
            False,
        ),
        ("Roles", ", ".join(r.mention for r in roles) if roles else "@everyone", False),
    ]

    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)

    await ctx.respond(embed=embed)


@misc_plugin.command
@lightbulb.add_cooldown(1, 5, lightbulb.UserBucket)
@lightbulb.command("serverinfo", "View info of the server")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
@hf.error_handler()
async def serverinfo(ctx: lightbulb.context.Context) -> None:
    guild = ctx.get_guild()
    members_mapping = guild.get_members()
    members = [member for member in members_mapping.values() if not member.is_bot]
    bots = [member for member in members_mapping.values() if member.is_bot]
    created_at = int(guild.created_at.timestamp())
    roles = guild.get_roles()
    embed = (
        hikari.Embed(color=EmbedColors.INFO, timestamp=datetime.now().astimezone())
        .set_thumbnail(guild.icon_url)
        .set_footer(text=f"Requested by {ctx.author}", icon=ctx.author.avatar_url)
    )
    fields = [
        ("ID", guild.id, True),
        ("Owner", f"<@{guild.owner_id}>", True),
        ("Members", len(members), True),
        ("Bots", len(bots), True),
        ("Created", f"<t:{created_at}:F> • <t:{created_at}:R>", True),
        ("Channel Count", len(guild.get_channels()), True),
        ("Boost Count", guild.premium_subscription_count, True),
        ("Premium Tier", str(guild.premium_tier).replace("_", " ").title(), True),
        ("Role Count", len(guild.get_roles()), True),
        (
            "Vanity URL",
            f"https://discord.gg/{guild.vanity_url_code}"
            if guild.vanity_url_code
            else "None",
            True,
        ),
        (
            "Roles",
            ", ".join(r.mention for r in roles.values() if not r.name == "@everyone"),
            False,
        ),
    ]

    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)

    if guild.features:
        embed.add_field(
            name="Guild Features",
            value="\n".join(
                "• " + feature.replace("_", " ").title() for feature in guild.features
            ),
            inline=False,
        )

    await ctx.respond(embed=embed)


@misc_plugin.command
@lightbulb.add_cooldown(1, 5, lightbulb.UserBucket)
@lightbulb.option(
    "remainder", "Text for the remainder", modifier=commands.OptionModifier.GREEDY
)
@lightbulb.option("time", "Time period for the remainder")
@lightbulb.command("remind", "Create a remainder")
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
async def remainder(ctx: lightbulb.context.Context) -> None:
    if ctx.interaction is None:
        remainder = " ".join(ctx.options.remainder)
    else:
        remainder = ctx.options.remainder
    time = ctx.options.time
    time_seconds = await convert_time(ctx, time)
    scheduler = fetch_scheduler(ctx)
    scheduler.add_job(
        send_remainder,
        "date",
        (ctx, remainder),
        next_run_time=datetime.now() + timedelta(seconds=int(time_seconds)),
    )

    await ctx.respond("Created a remainder for you! :ok_hand:")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(misc_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(misc_plugin)
