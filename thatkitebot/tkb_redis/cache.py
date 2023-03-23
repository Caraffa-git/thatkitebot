from datetime import timedelta, datetime
from typing import Union, Optional

import orjson
import brotli
import discord
from redis import asyncio as aioredis


from thatkitebot.base.image_stuff import get_image_urls, NoImageFoundException
from .exceptions import *

# TODO: make the cache actually store useful data alongside the message content

#  message id contains the time of message creation, that is pretty neat!
# so, we could make every message its own hash containing all sorts of potentially useful data

# alternatively we could have every channel be a hash, containing the messages as key - value pairs
# this would limit us in our ability to store much useful data other than the content
# this could be remedied by havign a "metadata" entry for every message, essentially doubling the numbers of entries required
# overall, this seems to be slower and more stupid
# alternatively we could serialize the whole message, not sure how useful that would be


class RedisCache:
    def __init__(self, redis: aioredis.Redis, bot: discord.Bot, auto_exec=False):
        self.redis: aioredis.Redis = redis
        self.bot: discord.Bot = bot

        self.auto_exec = auto_exec

        self.pipeline = redis.pipeline()

    def _sanity_check(self, message: discord.Message):
        # things we do not want to cache
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_system = message.is_system()
        is_me = message.author is self.bot.user
        return any((is_me, is_system, is_dm))

    async def add_message(self, message: discord.Message):
        """
        Adds a message to the cache. The message is stored in the following format: guild_id:channel_id:user_id:message_id
        """
        urls = []
        try:
            urls = await get_image_urls(message)
        except NoImageFoundException:
            pass

        if not message or self._sanity_check(message):
            raise CacheInvalidMessage

        hash_key = str(message.author.id)
        entry_key = f"{message.guild.id}:{message.channel.id}:{message.id}"

        dict_fun = dict(
            clean_content=message.clean_content,
            reference=message.reference.to_message_reference_dict() if message.reference else None,
            urls=urls
        )

        butt = orjson.dumps(dict_fun)
        data_compressed = brotli.compress(butt, quality=11)
        await self.pipeline.hset(hash_key, entry_key, data_compressed)
        await self.pipeline.hset("id_to_author", mapping={str(message.id): str(message.author.id)})
        await self.pipeline.hset("id_to_channel", mapping={str(message.id): str(message.channel.id)})
        await self.pipeline.expire(hash_key, timedelta(days=7))

        if self.auto_exec:
            await self.pipeline.execute()

    async def get_author_id(self, message_id: Union[int, str]):
        return int((await self.redis.hget("id_to_author", str(message_id))).decode("ASCII"))

    async def get_channel_id(self, message_id: Union[int, str]):
        return int((await self.redis.hget("id_to_channel", str(message_id))).decode("ASCII"))

    async def get_message(self, message_id: int, guild_id: int, channel_id: int | None = None, author_id: int | None = None):
        # get the message from the message_id
        # pretty stupid, but it works
        try:
            if not author_id:
                author_id = await self.get_author_id(message_id)

            if not channel_id:
                channel_id = await self.get_channel_id(message_id)
        except AttributeError:
            raise CacheInvalidMessage

        key = str(author_id)
        hash_key = f"{guild_id}:{channel_id}:{message_id}"


        #raw = [(key, data) async for key, data in self.redis.hscan_iter(str(author_id), match=f"*:{message_id}", count=1)]

        # make sure we actually got a key
        #if not raw:
        #    raise CacheInvalidMessage

        raw = await self.redis.hget(key, hash_key)

        if not raw:
            raise CacheInvalidMessage


        # decompress the data
        data_uncompressed = brotli.decompress(raw)

        # decode the json and turn it into a python dict
        data_decoded = orjson.loads(data_uncompressed)
        return hash_key, data_decoded

    async def exec(self):
        await self.pipeline.execute()





