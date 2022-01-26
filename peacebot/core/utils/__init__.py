import typing as t
from operator import attrgetter

_ValueT = t.TypeVar("_ValueT")
T = t.TypeVar("T")


def get(iterable: t.Iterable[T], **attrs: t.Any) -> t.Optional[T]:
    """A helper that returns the first element in the iterable that meets
    all the traits passed in ``attrs``.
    Args:
        iterable (Iterable): An iterable to search through.
        **attrs (Any): Keyword arguments that denote attributes to search with.
    """
    attrget = attrgetter

    # Special case the single element call
    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(k.replace("__", "."))
        for elem in iterable:
            if pred(elem) == v:
                return elem
        return None

    converted = [
        (attrget(attr.replace("__", ".")), value) for attr, value in attrs.items()
    ]

    for elem in iterable:
        if all(pred(elem) == value for pred, value in converted):
            return elem
    return None
