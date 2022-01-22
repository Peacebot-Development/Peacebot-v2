import lightbulb

from peacebot.core.utils.helper_functions import error_handler
from peacebot.core.utils.rtfm_helper import RTFMManager, SphinxObjectFileReader

rtfm_plugin = lightbulb.Plugin("RTFM", "RTFM Commands for the various Python modules")
languages = {
    "python": RTFMManager("python", "https://docs.python.org/3/"),
    "hikari": RTFMManager("hikari", "https://hikari-py.github.io/hikari/"),
    "lightbulb": RTFMManager(
        "lightbulb", "https://hikari-lightbulb.readthedocs.io/en/latest"
    ),
}


@rtfm_plugin.command
@lightbulb.command("rtfm", "Get docs for a module")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
@error_handler()
async def rtfm(ctx: lightbulb.Context) -> None:
    await ctx.bot.help_command.send_group_help(ctx, ctx.command)


@rtfm.child
@lightbulb.option("object", "The object or thing to search for")
@lightbulb.command("python", "Get references for Python")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
@error_handler()
async def rtfm_python(ctx: lightbulb.Context) -> None:
    response_python = await languages["python"].do_rtfm(ctx.options.object)
    await ctx.respond(response_python)


@rtfm.child
@lightbulb.option("object", "The object or thing to search for")
@lightbulb.command("hikari", "Get references for Hikari")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
@error_handler()
async def rtfm_hikari(ctx: lightbulb.Context) -> None:
    response_hikari = await languages["hikari"].do_rtfm(ctx.options.object)
    await ctx.respond(response_hikari)


@rtfm.child
@lightbulb.option("object", "The object or thing to search for")
@lightbulb.command("lightbulb", "Get references for Lightbulb")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
@error_handler()
async def rtfm_lightbulb(ctx: lightbulb.Context) -> None:
    response_lightbulb = await languages["lightbulb"].do_rtfm(ctx.options.object)
    await ctx.respond(response_lightbulb)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(rtfm_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(rtfm_plugin)
