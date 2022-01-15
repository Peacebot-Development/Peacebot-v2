import logging
import math
import re

import hikari
import lightbulb

from peacebot.core.utils.embed_colors import EmbedColors

logger = logging.getLogger("error_handler")


async def on_error(event: lightbulb.CommandErrorEvent) -> None:
    error = event.exception
    if isinstance(error, lightbulb.CommandNotFound):
        return

    if isinstance(error, lightbulb.BotMissingRequiredPermission):
        missing = [
            perm.replace("_", " ").replace("guild", "server").title()
            for perm in str(error.missing_perms).split("|")
        ]
        if len(missing) > 2:
            fmt = "{}, and {}".format("**, **".join(missing[:-1]), missing[-1])
        else:
            fmt = " and ".join(missing)

        _message = f"I need the **{fmt}** permission(s) to run this command."

        embed = hikari.Embed(
            title="I am Missing Permissions",
            color=EmbedColors.ALERT,
            description=_message,
        )
        return await event.context.respond(embed=embed)

    if isinstance(error, lightbulb.CommandIsOnCooldown):
        embed = hikari.Embed(
            title="Command on Cooldown",
            color=EmbedColors.ALERT,
            description=f"This command is on cooldown, please retry in {math.ceil(error.retry_after)}s.",
        )
        return await event.context.respond(embed=embed)

    if isinstance(error, lightbulb.NotEnoughArguments):
        return await event.bot.help_command.send_command_help(
            event.context, event.context.command
        )

    if isinstance(error, lightbulb.MissingRequiredPermission):
        missing = [
            perm.replace("_", " ").replace("guild", "server").title()
            for perm in str(error.missing_perms).split("|")
        ]
        if len(missing) > 2:
            fmt = "{}, and {}".format("**, **".join(missing[:-1]), missing[-1])
        else:
            fmt = " and ".join(missing)
        _message = "You need the **{}** permission(s) to use this command.".format(fmt)

        embed = hikari.Embed(
            title="You are missing permissions",
            color=EmbedColors.ALERT,
            description=_message,
        )
        return await event.context.respond(embed=embed)

    title = " ".join(re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__))
    await event.context.respond(
        embed=hikari.Embed(title=title, description=str(error), color=EmbedColors.ALERT)
    )
    raise error
