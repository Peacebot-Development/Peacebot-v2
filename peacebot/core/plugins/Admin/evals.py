import ast
import asyncio
import contextlib
import inspect
import io
import re
import time
import traceback
import typing as t
from collections import abc as collections
from datetime import timedelta

import hikari
import lightbulb
import yuyo
from lightbulb import commands

eval_plugin = lightbulb.Plugin("Evals")
eval_plugin.add_checks(lightbulb.owner_only)


def _yields_results(*args: io.StringIO) -> collections.Iterator[str]:
    for name, stream in zip(("stdout", "stderr"), args):
        yield f"-dev/{name}:"
        while lines := stream.readlines(25):
            yield from (line[:-1] for line in lines)


def build_eval_globals(ctx: lightbulb.context.Context) -> dict[str, t.Any]:
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
    ctx: lightbulb.context.Context, code: str
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


async def eval_python_code_no_capture(
    ctx: lightbulb.context.Context, code: str
) -> None:
    globals_ = build_eval_globals(ctx)
    compiled_code = compile(code, "", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    if compiled_code.co_flags & inspect.CO_COROUTINE:
        await eval(compiled_code, globals_)

    else:
        eval(compiled_code, globals_)


@eval_plugin.command
@lightbulb.command("eval", "Run Evals as Bot owner")
@lightbulb.implements(commands.PrefixCommand)
async def eval_command(ctx: lightbulb.context.Context) -> None:
    assert ctx.event.message is not None
    code = re.findall(
        r"```(?:[\w]*\n?)([\s\S(^\\`{3})]*?)\n*```", ctx.event.message.content
    )
    if not code:
        return await ctx.respond("Expected a python code block.")
    stdout, stderr, exec_time, failed = await eval_python_code(ctx, code[0])
    color = 0xFF0000 if failed else 0x00FF00
    string_paginator = yuyo.sync_paginate_string(
        _yields_results(stdout, stderr), wrapper="```python\n{}\n```", char_limit=2034
    )
    embed_generator = (
        (
            hikari.UNDEFINED,
            hikari.Embed(
                color=color, description=text, title=f"Eval Page {page}"
            ).set_footer(text=f"Time taken: {exec_time}ms"),
        )
        for text, page in string_paginator
    )
    response_paginator = yuyo.ComponentPaginator(
        embed_generator,
        authors=(ctx.author.id,),
        triggers=(
            yuyo.pagination.LEFT_DOUBLE_TRIANGLE,
            yuyo.pagination.LEFT_TRIANGLE,
            yuyo.pagination.STOP_SQUARE,
            yuyo.pagination.RIGHT_TRIANGLE,
            yuyo.pagination.RIGHT_DOUBLE_TRIANGLE,
        ),
        timeout=timedelta(seconds=60),
    )

    if first_response := await response_paginator.get_next_entry():
        content, embed = first_response
        response_proxy = await ctx.respond(
            content=content, component=response_paginator, embed=embed
        )
        message = await response_proxy.message()
        ctx.bot.d.component_client.set_executor(message.id, response_paginator)
        return


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(eval_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(eval_plugin)
