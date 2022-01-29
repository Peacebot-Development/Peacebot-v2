import hikari
import lightbulb

from models import GuildModel, ModerationRoles, ModLogs


class PermissionsError(lightbulb.LightbulbError):
    pass


async def has_permissions(
    member: hikari.Member, permission: list[hikari.Permissions]
) -> bool:
    roles = member.get_roles()
    perms = hikari.Permissions.NONE
    for role in roles:
        perms |= role.permissions

    permissions = str(perms).split("|")
    if set(permission) & set(permissions):
        return True
    return False


async def role_check(member: hikari.Member, role: hikari.Role) -> bool:
    if role.id in member.role_ids:
        return True
    return False


async def get_role_data(guild: hikari.Guild) -> dict:
    model = await ModerationRoles.get_or_none(guild_id=guild.id)
    if (
        model is None
        or model.admin_role is None
        or model.mod_role is None
        or model.moderation_role is None
    ):
        raise PermissionsError(
            "Some or all Moderation roles are not setup, Please set them and try again!\n`/help role` for more info."
        )

    admin_role = guild.get_role(model.admin_role)
    mod_role = guild.get_role(model.mod_role)
    moderation_role = guild.get_role(model.moderation_role)

    return {
        "admin_role": admin_role,
        "mod_role": mod_role,
        "moderation_role": moderation_role,
    }


def moderation_role_check(f):
    async def predicate(ctx: lightbulb.Context, *args, **kwargs):
        moderation_role: hikari.Role = (await get_role_data(ctx.get_guild())).get(
            "moderation_role"
        )
        if not (
            await has_permissions(ctx.member, ["MANAGE_MESSAGES", "ADMINISTRATOR"])
            or await role_check(ctx.member, moderation_role)
        ):
            raise PermissionsError(
                f"You need to have the permissions required to run this command!\nRole Required: {moderation_role.mention}"
            )
        return await f(ctx, *args, **kwargs)

    return predicate


def mod_role_check(f):
    async def predicate(ctx: lightbulb.Context, *args, **kwargs):
        mod_role: hikari.Role = (await get_role_data(ctx.get_guild())).get("mod_role")
        if not (
            await has_permissions(ctx.member, ["MANAGE_ROLES", "ADMINISTRATOR"])
            or await role_check(ctx.member, mod_role)
        ):
            raise PermissionsError(
                f"You need to have the permissions required to run this command!\nRole Required: {mod_role.mention}"
            )

        return await f(ctx, *args, **kwargs)

    return predicate


def admin_role_check(f):
    async def predicate(ctx: lightbulb.Context, *args, **kwargs):
        admin_role: hikari.Role = (await get_role_data(ctx.get_guild())).get(
            "admin_role"
        )
        if not (
            await has_permissions(ctx.member, ["ADMINISTRATOR"])
            or await role_check(ctx.member, admin_role)
        ):
            raise PermissionsError(
                f"You need to have the permissions required to run this command!\nRole Required: {admin_role.mention}"
            )
        return await f(ctx, *args, **kwargs)

    return predicate


def higher_role_check(author: hikari.Member, member: hikari.Member) -> None:
    """
    This function helps in checking the role heirarchy position of author and the member of the command invokation

    Parameters
    ----------
    author : hikari.Member
        Author of command invokation
    member : hikari.Member
        Member of the command invokation

    Raises
    ------
    PermissionsError
        Raised when author role position is not higher than member role
    """
    author_top_role = author.get_top_role()
    member_top_role = member.get_top_role()

    if not author_top_role.position > member_top_role.position:
        raise PermissionsError(
            "You cannot run moderation commands on this user, as they have got similar permissions and roles to yours."
        )


async def mod_logs_check(ctx: lightbulb.Context) -> hikari.GuildChannel:
    """
    This function helps in checking for Moderation Logging channel in a guild

    Parameters
    ----------
    ctx : lightbulb.Context
        Context of the Command Invokation

    Returns
    -------
    hikari.GuildChannel
        GuildChannel object of the Moderation Logging Channel

    Raises
    ------
    PermissionsError
        Raised when no Moderation Logging channel is set for the server
    """
    model = await GuildModel.get_or_none(id=ctx.guild_id)
    if model is None or model.mod_log_channel is None:
        raise PermissionsError(
            f"No Mod Logs channel found for the guild\nUse `/config modlog` to set."
        )
    channel = (ctx.get_guild()).get_channel(model.mod_log_channel)
    assert channel is not None
    return channel


async def delete_moderation_roles(model: ModerationRoles) -> None:
    if (
        model.admin_role is None
        and model.mod_role is None
        and model.moderation_role is None
    ):
        return await model.delete()
    pass


async def register_cases(
    guild_id: int,
    moderator: int,
    target: int,
    reason: str,
    message_link: str,
    channel_id: int,
    type: str,
) -> None:
    """
    This function helps in registering Moderation cases to the database

    Parameters
    ----------
    guild_id : int
        ID of the Guild where this moderation was performed
    moderator : int
        ID of the moderator who performed the action
    target : int
        ID of the target of the moderation action
    reason : str
        Reason due to which moderation action was taken
    message_link : str
        Link of the moderation message
    channel_id : int
        ID of the Channel where the action was performed
    type : str
        Type of Moderation Action, E.G => [Kick, Timeout Enable, Ban] etc.
    """
    await ModLogs.create(
        guild_id=guild_id,
        moderator=f"<@{moderator}>",
        target=f"<@{target}>",
        reason=reason,
        message=message_link,
        channel=f"<#{channel_id}>",
        type=type,
    )
