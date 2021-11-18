import logging

import hikari
import lightbulb

from peacebot.core.utils.embed_colors import EmbedColors


class CommandError(lightbulb.LightbulbError):
    pass


async def handle_plugins(
    ctx: lightbulb.context.Context, plugin_str: str, action: str
) -> None:
    try:
        getattr(ctx.bot, f"{action}_extensions")(plugin_str)
        logging.info(f"Plugin `{plugin_str}` has been {action}ed.")

    except lightbulb.ExtensionAlreadyLoaded:
        raise CommandError(f"Plugin `{plugin_str}` is already loaded.")
    except lightbulb.ExtensionNotLoaded:
        raise CommandError(f"Plugin `{plugin_str}` doesn't seem to be loaded.")

    await ctx.respond(
        embed=hikari.Embed(
            title=f"{action.title()} Plugin",
            description=f"`{plugin_str}` {action}ed sucessfully!",
            color=EmbedColors.INFO,
        )
    )
