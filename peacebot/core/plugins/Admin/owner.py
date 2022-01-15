import ast
import asyncio
import contextlib
import inspect
import io
import re
import time
import traceback
import typing as t

import hikari
import lightbulb
import yuyo
from lightbulb.utils import nav

import peacebot.core.utils.helper_functions as hf

from . import CommandError, handle_plugins

owner_plugin = lightbulb.Plugin("Owner", "Commands for bot owner")
owner_plugin.add_checks(lightbulb.owner_only)


def _yields_results(*args: io.StringIO) -> t.Iterator[str]:
    for name, stream in zip(("stdout", "stderr"), args):
        yield f"-dev/{name}:"
        while lines := stream.readlines(25):
            yield from (line[:-1] for line in lines)


def build_eval_globals(ctx: lightbulb.Context) -> dict[str, t.Any]:
    return {
        "asyncio": asyncio,
        "app": ctx.app,
        "bot": ctx.bot,
        "ctx": ctx,
        "hikari": hikari,
        "respond": ctx.respond,
        "lightbulb": lightbulb,
    }


async def eval_python_code(
    ctx: lightbulb.Context, code: str
) -> tuple[io.StringIO, io.StringIO, int, bool]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        with contextlib.redirect_stderr(stderr):
            start_time = time.perf_counter()
            try:
                await eval_python_code_no_capture(ctx, code)
                failed = False
            except Exception:
                traceback.print_exc()
                failed = True
            finally:
                exec_time = round((time.perf_counter() - start_time) * 1000)

    stdout.seek(0)
    stderr.seek(0)
    return stdout, stderr, exec_time, failed


async def eval_python_code_no_capture(ctx: lightbulb.Context, code: str) -> None:
    globals_ = build_eval_globals(ctx)
    compiled_code = compile(code, "", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    if compiled_code.co_flags & inspect.CO_COROUTINE:
        await eval(compiled_code, globals_)

    else:
        eval(compiled_code, globals_)


@owner_plugin.command
@lightbulb.set_help(docstring=True)
@lightbulb.command("eval", "Run Evals as Bot owner")
@lightbulb.implements(lightbulb.PrefixCommand)
@hf.error_handler()
async def eval_command(ctx: lightbulb.Context) -> None:
    """
    Dynamically evaluate a script in the bot's environment.
    This can only be used by the bot's owner.

    Example:
    ;eval py
    for x in range(5):
        print('Hello World')
    """
    assert ctx.event.message is not None
    code = re.findall(
        r"```(?:[\w]*\n?)([\s\S(^\\`{3})]*?)\n*```", ctx.event.message.content
    )
    if not code:
        raise CommandError("Expected a python code block.")
    stdout, stderr, exec_time, failed = await eval_python_code(ctx, code[0])
    color = 0xFF0000 if failed else 0x00FF00
    string_paginator = yuyo.sync_paginate_string(
        _yields_results(stdout, stderr), wrapper="```python\n{}\n```", char_limit=2034
    )
    fields = (
        hikari.Embed(
            color=color, description=text, title=f"Eval Page {page+1}"
        ).set_footer(text=f"Executed in: {exec_time}ms")
        for text, page in string_paginator
    )

    navigator = nav.ButtonNavigator(fields)
    await navigator.run(ctx)


@owner_plugin.command
@lightbulb.option("plugin", "Name of the plugin")
@lightbulb.command("reload", "Reload a specific plugin.")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
@hf.error_handler()
async def reload_plugin(ctx: lightbulb.Context) -> None:
    plugin = ctx.options.plugin
    await handle_plugins(ctx, plugin, "reload")


@owner_plugin.command
@lightbulb.option("plugin", "Name of the plugin")
@lightbulb.command("unload", "Unload a specific plugin.")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
@hf.error_handler()
async def unload_plugin(ctx: lightbulb.Context) -> None:
    plugin = ctx.options.plugin
    if plugin in [
        "peacebot.core.plugins.Admin.admin",
        "peacebot.core.plugins.Admin.owner",
    ]:
        raise CommandError(f"Cannot unload `{plugin}`")

    await handle_plugins(ctx, plugin, "unload")


@owner_plugin.command
@lightbulb.option("plugin", "Name of the plugin")
@lightbulb.command("load", "Load a specific plugin.")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
@hf.error_handler()
async def load_plugin(ctx: lightbulb.Context) -> None:
    plugin = ctx.options.plugin
    await handle_plugins(ctx, plugin, "load")


@owner_plugin.command
@lightbulb.command("shutdown", "Shutdown the Bot")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def shutdown(ctx: lightbulb.Context) -> None:
    await ctx.respond("Bot is shutting down, Bye Bye!")
    await ctx.bot.close()


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(owner_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(owner_plugin)
