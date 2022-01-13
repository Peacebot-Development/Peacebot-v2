import random
from datetime import datetime

import hikari
import lavasnek_rs
import lightbulb
from lightbulb import commands

from peacebot.core.utils.embed_colors import EmbedColors
from peacebot.core.utils.utilities import _chunk, paginate

from . import URL_REGEX, MusicError, _join, _leave, check_voice_state, fetch_lavalink

music_plugin = lightbulb.Plugin("Music")


@music_plugin.command
@lightbulb.add_cooldown(1, 5, lightbulb.UserBucket)
@lightbulb.set_help(docstring=True)
@lightbulb.command("join", "Join a voice channel of the guild")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def join(ctx: lightbulb.context.Context) -> None:
    """
    This command allows the bot to join a voice channel in a server.

    Parameters
    ----------
    None
    """
    channel_id = await _join(ctx)

    if channel_id:
        await ctx.respond(f"I joined <#{channel_id}>")


@music_plugin.command
# @lightbulb.set_help(docstring=True) # INFO: Potentially a Bug
@lightbulb.add_cooldown(2, 1, lightbulb.UserBucket)
@lightbulb.command("leave", "Leave the voice channel if already connected.")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
@check_voice_state
async def leave(ctx: lightbulb.context.Context) -> None:
    """
    This command makes the bot leave voice channel of a server.

    Parameters
    ----------
    None
    """
    await _leave(ctx)


@music_plugin.command
# @lightbulb.set_help(docstring=True) # INFO: Potentially a Bug
@lightbulb.option(
    "query", "Name or URL of the song", modifier=commands.OptionModifier.GREEDY
)
@lightbulb.command("play", "Play a song")
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
async def play(ctx: lightbulb.context.Context) -> None:
    """
    This command allows you to play songs in the voice channel.

    Parameters
    ----------
    query : str
        Name of the song or URL to the playlist.
    """
    lavalink = fetch_lavalink(ctx)
    if ctx.interaction is None:
        query = " ".join(ctx.options.query)
    else:
        query = ctx.options.query
    con = lavalink.get_guild_gateway_connection_info(ctx.guild_id)

    if not con:
        await _join(ctx)

    query_information = await lavalink.auto_search_tracks(query)
    if not query_information.tracks:
        raise MusicError("No songs found according to the query.")

    try:
        if not URL_REGEX.match(query):
            await lavalink.play(ctx.guild_id, query_information.tracks[0]).requester(
                ctx.author.id
            ).queue()
        else:
            for track in query_information.tracks:
                await lavalink.play(ctx.guild_id, track).requester(
                    ctx.author.id
                ).queue()

        node: lavasnek_rs.Node = await lavalink.get_guild_node(ctx.guild_id)
        if not node:
            pass
        else:
            node.set_data({ctx.guild_id: ctx.channel_id})
    except lavasnek_rs.NoSessionPresent:
        raise MusicError(f"Use `{ctx.prefix}`join to run this command.")

    embed = hikari.Embed(
        title="Tracks Added",
        description=f"[{query_information.tracks[0].info.title}]({query_information.tracks[0].info.uri})",
        color=EmbedColors.INFO,
    )

    await ctx.respond(embed=embed)


@music_plugin.command
# @lightbulb.set_help(docstring=True) # INFO: Potentially a Bug
@lightbulb.add_cooldown(2, 1, lightbulb.UserBucket)
@lightbulb.command("queue", "Shows the music queue for the guild")
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
async def queue(ctx: lightbulb.context.Context) -> None:
    """
    This command allows you to view the music queue for the server

    Parameters
    ----------
    None
    """
    lavalink = fetch_lavalink(ctx)
    song_queue = []
    node = await lavalink.get_guild_node(ctx.guild_id)
    if not node or not node.queue:
        raise MusicError("There are no tracks in the queue.")

    for song in node.queue:
        song_queue += [
            f"[{song.track.info.title}]({song.track.info.uri}) [<@{song.requester}>]"
        ]

    fields = []
    counter = 1
    if not len(song_queue[1:]) > 0:
        return await ctx.respond(
            f"No tracks in the queue.\n**Now Playing** : [{node.now_playing.track.info.title}]({node.now_playing.track.info.uri})"
        )
    for index, track in enumerate(_chunk(song_queue[1:], 8)):
        string = """**Next Up**\n"""
        temp = []
        for i in track:
            string += f"""{counter}. {i}\n"""

            counter += 1
        embed = hikari.Embed(
            title=f"Queue for {ctx.get_guild()}",
            color=EmbedColors.INFO,
            timestamp=datetime.now().astimezone(),
            description=string,
        )
        embed.set_footer(text=f"Page {index+1}")
        embed.add_field(
            name="Now Playing",
            value=f"[{node.now_playing.track.info.title}]({node.now_playing.track.info.uri}) [<@{node.now_playing.requester}>]",
        )
        temp.append(hikari.UNDEFINED)
        temp.append(embed)
        fields.append(temp)

    iter_fields = iter(fields)

    await paginate(ctx, iter_fields, 180)


@music_plugin.command
# @lightbulb.set_help(docstring=True) # INFO: Potentially a Bug
@lightbulb.add_cooldown(2, 1, lightbulb.UserBucket)
@lightbulb.command("pause", "Pause the currently playing song.")
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
@check_voice_state
async def pause(ctx: lightbulb.context.Context) -> None:
    """
    This command allows you to pause the currently playing song.

    Parameters
    ----------
    None
    """
    lavalink = fetch_lavalink(ctx)
    node = await lavalink.get_guild_node(ctx.guild_id)
    if not node or not node.now_playing:
        raise MusicError("There are no tracks playing currently!")

    if node.is_paused:
        raise MusicError("Playback seems to be already paused.")

    await lavalink.pause(ctx.guild_id)
    await lavalink.set_pause(ctx.guild_id, True)

    await ctx.respond("⏸️ Paused..")


@music_plugin.command
# @lightbulb.set_help(docstring=True) # INFO: Potentially a Bug
@lightbulb.add_cooldown(2, 1, lightbulb.UserBucket)
@lightbulb.command("resume", "Resume the paused track.")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
@check_voice_state
async def resume(ctx: lightbulb.context.Context) -> None:
    """
    This command allows you to resume the paused song.
    If already resumed, it throws an error.

    Parameters
    ----------
    None
    """
    lavalink = fetch_lavalink(ctx)
    node = await lavalink.get_guild_node(ctx.guild_id)

    if not node or not node.now_playing:
        raise MusicError("There are no tracks playing currently!")

    if node.is_paused:
        await lavalink.resume(ctx.guild_id)
        await ctx.respond("🎵 Playback resumed.")
    else:
        raise MusicError(
            "Looks like it's resumed already\nI don't know what you are trying to resume 😕"
        )


@music_plugin.command
# @lightbulb.set_help(docstring=True) # INFO: Potentially a Bug
@lightbulb.add_cooldown(2, 1, lightbulb.UserBucket)
@lightbulb.command("shuffle", "Shuffle the current queue")
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
@check_voice_state
async def shuffle(ctx: lightbulb.context.Context) -> None:
    """
    This command allows you to shuffle the queue in the server.
    Raises error there is only one track in the queue

    Parameters
    ----------
    None
    """
    lavalink = fetch_lavalink(ctx)
    node = await lavalink.get_guild_node(ctx.guild_id)

    if not len(node.queue) > 1:
        raise MusicError("Cannot shuffle a single song 🥴")

    queue = node.queue[1:]
    random.shuffle(queue)
    queue.insert(0, node.queue[0])

    node.queue = queue
    await lavalink.set_guild_node(ctx.guild_id, node)

    await ctx.respond("🔀 Queue has been shuffled.")


@music_plugin.command
# @lightbulb.set_help(docstring=True) # INFO: Potentially a Bug
@lightbulb.add_cooldown(2, 1, lightbulb.UserBucket)
@lightbulb.command("skip", "Skip the song that's currently playing.")
# @lightbulb.bot_has_guild_permissions(
#     hikari.Permissions.CONNECT
#     | hikari.Permissions.SPEAK
#     | hikari.Permissions.VIEW_CHANNEL
#     | hikari.Permissions.SEND_MESSAGES
# )
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
@check_voice_state
async def skip(ctx: lightbulb.context.Context) -> None:
    """
    This command allows you to skip the currently playing song.
    If there are no more tracks in the queue, it stops the playback.

    Parameters
    ----------
    None
    """
    lavalink = fetch_lavalink(ctx)
    skip = await lavalink.skip(ctx.guild_id)
    node = await lavalink.get_guild_node(ctx.guild_id)

    if not skip:
        raise MusicError("I don't see any tracks to skip 😕")

    if not node.queue and not node.now_playing:
        await lavalink.stop(ctx.guild_id)

    embed = hikari.Embed(
        title="⏭️ Skipped",
        color=EmbedColors.INFO,
        description=f"[{skip.track.info.title}]({skip.track.info.uri})",
    )

    await ctx.respond(embed=embed)


@music_plugin.command
# @lightbulb.set_help(docstring=True) # INFO: Potentially a Bug
@lightbulb.add_cooldown(2, 1, lightbulb.UserBucket)
@lightbulb.command("stop", "Stop the playback")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
@check_voice_state
async def stop(ctx: lightbulb.context.Context) -> None:
    """
    This command allows you the stop the playback in the server.

    Note: This also clears the queue.

    Parameters
    ----------
    None
    """
    lavalink = fetch_lavalink(ctx)
    await lavalink.stop(ctx.guild_id)

    await ctx.respond("⏹️ Playback has been stopped.")


@music_plugin.command
# @lightbulb.set_help(docstring=True) # INFO: Potentially a Bug
@lightbulb.add_cooldown(2, 1, lightbulb.UserBucket)
@lightbulb.command("song", "Commands for songs")
@lightbulb.implements(commands.SlashCommandGroup, commands.PrefixCommandGroup)
async def song(ctx: lightbulb.context.Context) -> None:
    """
    Command group that deals with moving and removing songs from the queue.

    Parameters
    ----------
    None
    """
    await ctx.bot.help_command.send_group_help(ctx, ctx.command)


@song.child
# @lightbulb.set_help(docstring=True) # INFO: Potentially a Bug
@lightbulb.add_cooldown(2, 1, lightbulb.UserBucket)
@lightbulb.option(
    name="new_index", description="New index at which song is to be moved", type=int
)
@lightbulb.option(name="old_index", description="Song to move", type=int)
@lightbulb.command("move", "Move song to specific index in the queue")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
@check_voice_state
async def move(ctx: lightbulb.context.Context) -> None:
    """
    This command allows you to move a song to a new index.

    Parameters
    ----------
        old_index : int
            Index of the song to be moved.

        new_index : int
            Index at which song is to be moved.
    """
    lavalink = fetch_lavalink(ctx)
    new_index = int(ctx.options.new_index)
    old_index = int(ctx.options.old_index)

    node = await lavalink.get_guild_node(ctx.guild_id)
    if not len(node.queue) >= 1:
        raise MusicError("There seems to be only one song in the queue.")

    queue = node.queue
    song_to_be_moved = queue[old_index]

    try:
        queue.pop(old_index)
        queue.insert(new_index, song_to_be_moved)

    except KeyError:
        raise MusicError(
            "There is no song at the given index.\nCheck the queue and try again"
        )

    node.queue = queue

    await lavalink.set_guild_node(ctx.guild_id, node)
    embed = hikari.Embed(
        title=f"Moved `{song_to_be_moved.track.info.title}` to Position `{new_index}`",
        color=EmbedColors.INFO,
    )
    await ctx.respond(embed=embed)


@song.child
# @lightbulb.set_help(docstring=True) # INFO: Potentially a Bug
@lightbulb.option("index", "Index of song to be removed", type=int)
@lightbulb.command("remove", "Remove a song from the queue")
@lightbulb.implements(commands.SlashSubCommand, commands.PrefixSubCommand)
@check_voice_state
async def remove_song(ctx: lightbulb.context.Context) -> None:
    """
    This command allows you to remove a specific song from the queue.

    Parameters
    ----------
    index : int
            Index of the song to be removed
    """
    lavalink = fetch_lavalink(ctx)
    index = ctx.options.index
    node = await lavalink.get_guild_node(ctx.guild_id)
    if not node.queue:
        raise MusicError("No songs in the queue")

    if index == 0:
        raise MusicError(
            f"You cannot remove a song that's playing now.\nUse {ctx.prefix}skip to skip the song."
        )

    queue = node.queue
    song_to_be_removed = queue[index]

    try:
        queue.pop(index)
    except IndexError:
        raise MusicError("No such song exists at the index you provided.")

    node.queue = queue
    await lavalink.set_guild_node(ctx.guild_id, node)
    embed = hikari.Embed(
        title=f"Removed `{song_to_be_removed.track.info.title}` from the queue.",
        color=EmbedColors.INFO,
    )
    await ctx.respond(embed=embed)


@music_plugin.command
@lightbulb.command("nowplaying", "See currently playing track's info", aliases=["np"])
@lightbulb.implements(commands.SlashCommand, commands.PrefixCommand)
async def nowplaying(ctx: lightbulb.context.Context) -> None:
    lavalink = fetch_lavalink(ctx)
    node = await lavalink.get_guild_node(ctx.guild_id)

    if not node or not node.now_playing:
        raise MusicError("There's nothing playing at the moment!")

    embed = hikari.Embed(
        title="Now Playing",
        description=f"[{node.now_playing.track.info.title}]({node.now_playing.track.info.uri})",
        color=EmbedColors.INFO,
    )
    fields = [
        ("Requested by", f"<@{node.now_playing.requester}>", True),
        ("Author", node.now_playing.track.info.author, True),
    ]
    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)
    await ctx.respond(embed=embed)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(music_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(music_plugin)
