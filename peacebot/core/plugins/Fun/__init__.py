import asyncio
import functools
import pickle
import typing

import aiofiles
from asyncpraw import Reddit
from lightbulb import context
from pydantic import BaseModel

from peacebot.config.reddit import reddit_config


class RedditSubmission(BaseModel):
    url: str
    title: str
    permalink: str


class RedditCacher:
    def __init__(
        self,
        cache_file_path: str,
        cached_posts_count: int | None = 100,
        subreddits: set[str] | None = None,
        cache_refresh_time: int | None = 60 * 60 * 6,
    ) -> None:
        self._cache_file_path = cache_file_path
        self._subreddits = subreddits or set()
        self._cache_refresh_time = cache_refresh_time
        self._cached_posts_count = cached_posts_count
        self._reddit = Reddit(
            client_id=reddit_config.client_id,
            client_secret=reddit_config.client_secret,
            user_agent="Peace Bot",
        )
        self.__start_caching = False

        asyncio.create_task(self._cache_loop())

    def command(self, subreddit_name: str) -> typing.Callable:
        def predicate(func: typing.Callable) -> typing.Callable:
            @functools.wraps(func)
            async def inner_function(ctx: context.Context) -> typing.Callable:
                if not hasattr(func, "__is_cached__"):
                    data = await self._generate_single_subreedit_cache(subreddit_name)
                    async with aiofiles.open(self._cache_file_path, "wb+") as f:
                        file_data = await f.read()
                        cache = pickle.loads(file_data) if file_data else {}
                        cache[subreddit_name] = data
                        await f.write(pickle.dumps(cache))

                    setattr(func, "__is_cached__", True)
                    self._subreddits.add(subreddit_name)

                return await func(ctx)

            return inner_function

        return predicate

    async def get_subreddit_posts(self, subreddit_name: str) -> list[RedditSubmission]:
        async with aiofiles.open(self._cache_file_path, "rb") as f:
            data = pickle.loads(await f.read())

        if posts := data.get(subreddit_name):
            return [RedditSubmission(**post) for post in posts]
        return None

    async def _cache_loop(self) -> None:
        # Waits for proper initialization
        await asyncio.sleep(20)

        self.__start_caching = True

        while self.__start_caching:
            if not self._subreddits:
                await asyncio.sleep(self._cache_refresh_time)
                continue

            data_to_dump = await self._generate_subreddit_cache(self._subreddits)
            async with aiofiles.open(self._cache_file_path, mode="wb+") as f:
                await f.write(pickle.dumps(data_to_dump))

            await asyncio.sleep(self._cache_refresh_time)

    async def stop_caching(self) -> None:
        self.__start_caching = False

    async def _generate_single_subreedit_cache(self, subreddit_name: str):
        subreddit = await self._reddit.subreddit(subreddit_name, fetch=True)
        posts = [
            {
                "url": post.url,
                "title": post.title,
                "permalink": post.permalink,
            }
            async for post in subreddit.hot(limit=self._cached_posts_count)
        ]

        allowed_extensions = (".gif", ".png", ".jpg", ".jpeg")
        posts = list(
            filter(
                lambda i: any((i.get("url").endswith(e) for e in allowed_extensions)),
                posts,
            )
        )

        return posts

    async def _generate_subreddit_cache(self, subreddits: list[str]) -> dict[str, str]:
        # Not using asyncio.gather as the API will be ratelimited
        return {
            subreddit: await self._generate_single_subreedit_cache(subreddit)
            for subreddit in subreddits
        }
