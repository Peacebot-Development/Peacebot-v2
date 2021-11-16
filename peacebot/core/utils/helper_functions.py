import functools
import logging
import typing as t

import lightbulb
from lightbulb import LightbulbError

logger = logging.getLogger(__name__)


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
