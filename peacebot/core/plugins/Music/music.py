import lightbulb
from lightbulb import commands

from . import _join, _leave, check_voice_state, music_plugin


@music_plugin.command
@lightbulb.command("join", "Join a voice channel of the guild")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def join(ctx: lightbulb.context.Context) -> None:
    channel_id = await _join(ctx)

    if channel_id:
        await ctx.respond(f"I joined <#{channel_id}>")


@music_plugin.command
@lightbulb.command("leave", "Leave the voice channel if already connected.")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
@check_voice_state
async def leave(ctx: lightbulb.context.Context) -> None:
    await _leave(ctx)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(music_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(music_plugin)
