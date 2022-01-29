from __future__ import annotations

import typing as t

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
