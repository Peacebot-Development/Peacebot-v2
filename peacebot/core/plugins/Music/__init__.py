# import re

import lavasnek_rs
import lightbulb

__all__ = ["_join", "_leave", "check_voice_state", "fetch_lavalink"]

# URL_REGEX = re.compile(
#     r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
# )


class MusicError(lightbulb.LightbulbError):
    pass


async def _join(ctx: lightbulb.Context) -> int:
    lavalink = fetch_lavalink(ctx.bot)
    if ctx.bot.cache.get_voice_state(ctx.get_guild(), ctx.bot.get_me()):
        raise MusicError("I am already connected to another Voice Channel.")
    states = ctx.bot.cache.get_voice_states_view_for_guild(ctx.get_guild())
    voice_state = list(filter(lambda i: i.user_id == ctx.author.id, states.iterator()))

    if not voice_state:
        raise MusicError("Connect to a voice channel to continue!")

    channel_id = voice_state[0].channel_id

    try:
        connection_info = await lavalink.join(ctx.guild_id, channel_id)

    except TimeoutError:
        raise MusicError("I cannot connect to your voice channel!")

    await lavalink.create_session(connection_info)
    node = await lavalink.get_guild_node(ctx.guild_id)
    node.set_data({ctx.guild_id: ctx.channel_id})
    return channel_id


async def _leave(ctx: lightbulb.Context):
    lavalink = fetch_lavalink(ctx.bot)
    await lavalink.destroy(ctx.guild_id)
    await lavalink.stop(ctx.guild_id)
    await lavalink.leave(ctx.guild_id)
    await lavalink.remove_guild_node(ctx.guild_id)
    await lavalink.remove_guild_from_loops(ctx.guild_id)

    await ctx.respond("I left the voice channel!")


def check_voice_state(f):
    async def predicate(ctx: lightbulb.Context, *args, **kwargs):
        guild = ctx.get_guild()
        bot_user = ctx.bot.get_me()

        voice_state_bot = ctx.bot.cache.get_voice_state(guild, bot_user)
        voice_state_author = ctx.bot.cache.get_voice_state(guild, ctx.author)

        if voice_state_bot is None:
            raise MusicError(
                f"I am not connected to any Voice Channel.\nUse `{ctx.prefix}join` to connect me to one."
            )

        if voice_state_author is None:
            raise MusicError(
                "You are not in a Voice Channel, Join a Voice Channel to continue."
            )

        if not voice_state_author.channel_id == voice_state_bot.channel_id:
            raise MusicError(
                "I cannot run this command as you are not in the same voice channel as me."
            )

        return await f(ctx, *args, **kwargs)

    return predicate


def fetch_lavalink(bot: lightbulb.BotApp) -> lavasnek_rs.Lavalink:
    return bot.d.data.lavalink
