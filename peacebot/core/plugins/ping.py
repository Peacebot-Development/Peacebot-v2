import lightbulb
from lightbulb import commands

ping_plugin = lightbulb.Plugin("Ping")


@ping_plugin.command
@lightbulb.command("ping", "Check if bot is alive or not")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def ping(ctx: lightbulb.context.Context) -> None:
    await ctx.respond(f"Pong! {int(ctx.bot.heartbeat_latency*1000)}ms")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(ping_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(ping_plugin)
