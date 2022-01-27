import functools
import logging
import math
import re
import typing as t
from datetime import datetime, timedelta

import lightbulb
from lightbulb import LightbulbError

from .errors import HelpersError

logger = logging.getLogger(__name__)

time_regex = re.compile("(?:(\d{1,5})(h|s|m|d|w))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400, "w": 604800}

ordinal = lambda n: "%d%s" % (
    n,
    "tsnrhtdd"[(math.floor(n / 10) % 10 != 1) * (n % 10 < 4) * n % 10 :: 4],
)


steps = dict(
    year=timedelta(days=365),
    week=timedelta(days=7),
    day=timedelta(days=1),
    hour=timedelta(hours=1),
    minute=timedelta(minutes=1),
    second=timedelta(seconds=1),
    millisecond=timedelta(milliseconds=1),
)


class CommandError(LightbulbError):
    pass


def error_handler(error_mapping: t.Optional[dict[Exception, str]] = None):
    def prediate(func: t.Callable) -> t.Callable:
        @functools.wraps(func)
        async def wrapper(
            ctx: lightbulb.context.Context, *args, **kwargs
        ) -> t.Callable:
            try:
                return await func(ctx, *args, **kwargs)
            except Exception as e:
                if isinstance(e, LightbulbError):
                    raise e

                logging.info(error_mapping)
                error_map = error_mapping or {}
                error = error_map.get(e.__class__) or str(e)
                logging.info(error)

                raise CommandError(
                    f"An error ({e.__class__.__name__}) occured in **{ctx.command.name}:** ```py\n{error}```"
                )

        return wrapper

    return prediate


def convert_time(argument: str) -> float:
    args = argument.lower()
    matches = re.findall(time_regex, args)
    time = 0
    for value, key in matches:
        try:
            time += time_dict[key] * float(value)
        except KeyError:
            raise HelpersError(
                f"{key} is an invalid time key!\nThe valid keys are h/m/s/d"
            )
        except ValueError:
            raise HelpersError(f"{value} is not a number.")

    return time


def pretty_timedelta(td: timedelta) -> str:
    """Returns a pretty string of a timedelta"""

    if not isinstance(td, timedelta):
        raise ValueError("timedelta expected, '{}' given".format(type(td)))

    parts = []

    for name, span in steps.items():
        if td >= span:
            count = int(td / span)
            td -= count * span
            parts.append("{} {}{}".format(count, name, "s" if count > 1 else ""))
            if len(parts) >= 2 or name == "second":
                break
        elif len(parts):
            break

    return ", ".join(parts)


def pretty_seconds(s) -> str:
    return pretty_timedelta(timedelta(seconds=s))


def pretty_datetime(dt: datetime, ignore_time=False) -> str:
    if not isinstance(dt, datetime):
        raise ValueError("datetime expected, '{}' given".format(type(dt)))

    return "{0} {1}".format(
        ordinal(int(dt.strftime("%d"))),
        dt.strftime("%b %Y" + ("" if ignore_time else " %H:%M")),
    )


def time_mult_converter(mult: str) -> float:
    try:
        mult = float(mult)
    except ValueError:
        raise HelpersError("Argument has to be float.")

    if mult < 1.0:
        raise HelpersError("Unit must be more than 1.")

    return mult


def timedelta_converter(unit: str):
    unit = unit.lower()

    if unit in ("s", "sec", "secs", "second", "seconds"):
        return timedelta(seconds=1)
    elif unit in ("m", "min", "mins", "minute", "minutes"):
        return timedelta(minutes=1)
    elif unit in ("h", "hr", "hrs", "hour", "hours"):
        return timedelta(hours=1)
    elif unit in ("d", "day", "days"):
        return timedelta(days=1)
    elif unit in ("w", "wk", "week", "weeks"):
        return timedelta(weeks=1)
    else:
        raise HelpersError("Unknown time type.")
