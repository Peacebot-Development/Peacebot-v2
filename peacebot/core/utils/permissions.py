import hikari
import lightbulb

from models import ModerationRoles

from . import get


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


async def higher_role_check(author: hikari.Member, member: hikari.Member) -> None:
    author_top_role = author.get_top_role()
    member_top_role = member.get_top_role()

    if not author_top_role.position > member_top_role.position:
        raise PermissionsError(
            "You cannot run moderation commands on this user, as they have got similar permissions and roles to yours."
        )
