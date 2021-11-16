from __future__ import annotations

import typing as t
from datetime import timedelta

import lightbulb
import yuyo

_ValueT = t.TypeVar("_ValueT")
T = t.TypeVar("T")


def _chunk(iterator: t.Iterator[_ValueT], max: int) -> t.Iterator[list[_ValueT]]:
    chunk: list[_ValueT] = []
    for entry in iterator:
        chunk.append(entry)
        if len(chunk) == max:
            yield chunk
            chunk = []

    if chunk:
        yield chunk


async def paginate(
    ctx: lightbulb.context.Context,
    fields: t.Generator[tuple | list],
    timeout: float | str,
):
    paginator = yuyo.ComponentPaginator(
        fields,
        authors=(ctx.author.id,),
        timeout=timedelta(seconds=timeout),
        triggers=(
            yuyo.pagination.LEFT_DOUBLE_TRIANGLE,
            yuyo.pagination.LEFT_TRIANGLE,
            yuyo.pagination.STOP_SQUARE,
            yuyo.pagination.RIGHT_TRIANGLE,
            yuyo.pagination.RIGHT_DOUBLE_TRIANGLE,
        ),
    )

    if first_response := await paginator.get_next_entry():
        content, embed = first_response
        response_proxy = await ctx.respond(
            content=content,
            component=paginator,
            embed=embed,
        )

        message = await response_proxy.message()
        ctx.bot.d.component_client.set_executor(message.id, paginator)
        return
