import functools
import logging
import re
import typing as t

import lightbulb
from lightbulb import LightbulbError

from .errors import HelpersError

logger = logging.getLogger(__name__)

time_regex = re.compile("(?:(\d{1,5})(h|s|m|d|w))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400, "w": 604800}


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
