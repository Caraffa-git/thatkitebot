#region License
"""
MIT License

Copyright (c) 2019-present The Kitebot Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
#endregion

#region imports
from typing import Union

from redis import asyncio as aioredis
#endregion

class RedisQueue:
    __slots__ = ("_queue_len", "_redis", "queue_name", "_expire_after")

    def __init__(self, session, queue_name: str, expire_after=None):
        self.queue_name = queue_name
        self._redis: aioredis.Redis = session
        self._queue_len = 0
        self._expire_after = expire_after

    def __len__(self):
        return self._queue_len

    async def update_length(self):
        new_length = await self._redis.llen(self.queue_name)
        self._queue_len = new_length
        return new_length

    async def pop(self):
        popped = await self._redis.rpop(name=self.queue_name)
        await self.update_length()
        return popped

    async def push(self, *values: Union[str, int, bytes]):
        await self._redis.lpush(self.queue_name, *values)
        if self._expire_after:
            await self._redis.expire(self.queue_name, self._expire_after)
        await self.update_length()

    async def move(self, source_index, destination_index):
        # smh aioredis has no lmove
        # https://redis.io/commands/lmove
        # this is a workaround

        if source_index == destination_index:
            return
        # make sure the indexes are in range
        await self.update_length()
        if source_index >= self._queue_len or destination_index >= self._queue_len:
            raise IndexError("Index out of range")
        old_value = await self._redis.lindex(self.queue_name, source_index)
        # Remove the old value
        await self._redis.lrem(self.queue_name, 1, old_value)
        # Insert the old value at the new index
        await self._redis.linsert(self.queue_name, "BEFORE", destination_index, old_value)
        # Update the length of the queue

    async def shuffle(self):
        raise NotImplementedError("Shuffling is not implemented yet.")

    async def clear(self):
        await self._redis.delete(self.queue_name)
        self._queue_len = 0

    async def list_all(self):
        await self.update_length()
        return await self._redis.lrange(self.queue_name, 0, self._queue_len)

    async def output_generator(self):
        while out_data := await self.pop():
            yield out_data

    async def output_generator_nondestructive(self):
        for i in range(self._queue_len):
            yield await self._redis.lindex(self.queue_name, i)