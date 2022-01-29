import io
import os
import re
import typing
import zlib
from datetime import datetime

import aiohttp
import hikari
from rapidfuzz import fuzz, process

from peacebot.core.utils.embed_colors import EmbedColors


class SphinxObjectFileReader:
    BUFSIZE = 16 * 1024

    def __init__(self, buffer):
        self.stream = io.BytesIO(buffer)

    def readline(self):
        return self.stream.readline().decode("utf-8")

    def skipline(self):
        self.stream.readline()

    def read_compressed_chunks(self):
        decompressor = zlib.decompressobj()
        while True:
            chunk = self.stream.read(self.BUFSIZE)
            if len(chunk) == 0:
                break
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def read_compressed_lines(self):
        buf = b""
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b"\n")
            while pos != -1:
                yield buf[:pos].decode("utf-8")
                buf = buf[pos + 1 :]
                pos = buf.find(b"\n")


class RTFMManager:
    def __init__(self, slug, url):
        self._slug = slug
        self._url = url
        self._rtfm_cache = {}

    def purge_cache(self):
        del self._rtfm_cache

    def parse_object_inv(self, stream, url):
        # key: URL
        result = {}

        # first line is version info
        inv_version = stream.readline().rstrip()

        if inv_version != "# Sphinx inventory version 2":
            raise RuntimeError("Invalid objects.inv file version.")

        # next line is "# Project: <name>"
        # then after that is "# Version: <version>"
        projname = stream.readline().rstrip()[11:]
        version = stream.readline().rstrip()[11:]

        # next line says if it's a zlib header
        line = stream.readline()
        if "zlib" not in line:
            raise RuntimeError("Invalid objects.inv file, not z-lib compatible.")

        # This code mostly comes from the Sphinx repository.
        entry_regex = re.compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)")
        for line in stream.read_compressed_lines():
            match = entry_regex.match(line.rstrip())
            if not match:
                continue

            name, directive, prio, location, dispname = match.groups()
            domain, _, subdirective = directive.partition(":")
            if directive == "py:module" and name in result:
                # From the Sphinx Repository:
                # due to a bug in 1.1 and below,
                # two inventory entries are created
                # for Python modules, and the first
                # one is correct
                continue

            # Most documentation pages have a label
            if directive == "std:doc":
                subdirective = "label"

            if location.endswith("$"):
                location = location[:-1] + name

            key = name if dispname == "-" else dispname
            prefix = f"{subdirective}:" if domain == "std" else ""

            remove_pref = f"{prefix}{key}".startswith(self._slug + ".")
            result[
                f"{prefix}{key}"[len(self._slug + ".") if remove_pref else 0 :]
            ] = os.path.join(url, location)

        return result

    async def build_rtfm_lookup_table(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url + "/objects.inv") as resp:
                if resp.status != 200:
                    raise RuntimeError(
                        "Cannot build rtfm lookup table, try again later."
                    )

                stream = SphinxObjectFileReader(await resp.read())
                cache = self.parse_object_inv(stream, url)

        self._rtfm_cache = cache

    async def do_rtfm(self, obj: str) -> str | hikari.Embed:
        if obj is None:
            return self._url

        if not self._rtfm_cache:
            await self.build_rtfm_lookup_table(self._url)

        matches = process.extract(
            obj, self._rtfm_cache.keys(), scorer=fuzz.QRatio, limit=10
        )

        e = hikari.Embed(colour=EmbedColors.INFO, title=f"RTFM for {obj}").set_footer(
            text=f"Module: {self._slug}"
        )
        if len(matches) == 0:
            return "Could not find anything. Sorry."

        e.description = "\n".join(
            f"[`{key}`]({self._rtfm_cache[key]})" for key, _, __ in matches
        )
        return e
