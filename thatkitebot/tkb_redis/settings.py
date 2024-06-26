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
import enum
from typing import Union


from discord import Guild
from redis import asyncio as aioredis

from .exceptions import InvalidGuildException
#endregion

#region main class
class RedisFlags:
    class FlagEnum(enum.Enum):
        NSFW = 0
        IMAGE = 1
        REPOST = 2
        WELCOME = 3
        UWU = 4
        DETRACK = 5
        MUSIC = 6
        CACHING = 7
        WELCOME_MESSAGE = 8
        MODERATION = 9
        STARBOARD = 10


    @staticmethod
    async def set_guild_flag(redis: aioredis.Redis, gid: Union[Guild, int, None], flag_offset: FlagEnum, value: bool) -> int:
        """
        Sets flags for a guild. They are stored as Bitfields. The flags are stored at the following offsets:
        0: NSFW (nsfwcog.py) - NSFW commands
        1: IMAGES (imagecog.py) - Image commands
        3: WELCOME COUNTING (welcomecog.py) - Welcome Counting
        4: UWUIFICATION (uwucog.py) - uwuify
        5: LINK DETRACKING (detrack.py) - detracking
        6: MUSIC (musiccog.py) - music commands
        7: CACHING
        8: WELCOME MESSAGE
        9: MODERATION
        10: STARBOARD (Disable-Flag, 1 = Disabled 0 = Enabled)
        """
        # raise invalid guild exception if command is somehow doesn't get a guild id or guild object
        if not gid:
            raise InvalidGuildException
        
        if isinstance(gid, int):
            guild_id = gid
        elif isinstance(gid, Guild):
            guild_id = gid.id

        return await redis.setbit(f"flags:{guild_id}", flag_offset.value, int(value))

    @staticmethod
    async def get_guild_flag(redis: aioredis.Redis, guild: Union[Guild, int, None], flag_offset: FlagEnum) -> bool:
        """
        Sets flags for a guild. They are stored as Bitfields. The flags are stored at the following offsets:
        0: NSFW (nsfwcog.py) - NSFW commands
        1: IMAGES (imagecog.py) - Image commands
        3: WELCOME COUNTING (welcomecog.py) - Welcome Counting
        4: UWUIFICATION (uwucog.py) - uwuify
        5: LINK DETRACKING (detrack.py) - detracking
        6: MUSIC (musiccog.py) - music commands
        7: CACHING
        8: WELCOME MESSAGE
        9: MODERATION
        10: STARBOARD (Disable-Flag, 1 = Disabled 0 = Enabled)
        """
        if guild is not None:
            if isinstance(guild, int):
                guild_id = guild
            elif isinstance(guild, Guild):
                guild_id = guild.id

            return await redis.getbit(f"flags:{guild_id}", flag_offset.value)
        else:
            return True
        
    @staticmethod
    async def set_guild_flag_custom(redis: aioredis.Redis, gid: Union[Guild, int, None], name: str, value: bool, flag_offset: int) -> int:
        """
        Sets flags for a guild with a custom name. They are stored as Bitfields.
        """
        if isinstance(gid, int):
            guild_id = gid
        elif isinstance(gid, Guild):
            guild_id = gid.id

        return await redis.setbit(f"flags-{name}:{guild_id}", flag_offset, int(value))

    @staticmethod
    async def get_guild_flag_custom(redis: aioredis.Redis, gid: Union[Guild, int], name: str, flag_offset: int) -> bool:
        """
        Gets flags for a guild with a custom name. They are stored as Bitfields.
        """
        if not gid:
            return False
        
        if isinstance(gid, int):
            guild_id = gid
        elif isinstance(gid, Guild):
            guild_id = gid.id

        return bool(await redis.getbit(f"flags-{name}:{guild_id}", flag_offset))

    @staticmethod
    async def get_guild_flags(redis: aioredis.Redis, gid: Union[Guild, int], *flag_offsets: FlagEnum) -> list[bool]:
        """
        Checks multiple flags at once, useful for checking multiple flags at once
        """
        if isinstance(gid, int):
            guild_id = gid
        elif isinstance(gid, Guild):
            guild_id = gid.id
        
        items = [("u1", offset.value) for offset in flag_offsets]

        return [bool(value) for value in await redis.bitfield_ro(f"flags:{guild_id}", "u1", 0, items=items)]

    @staticmethod
    async def toggle_guild_flag(redis: aioredis.Redis, gid: Union[Guild, int, None], flag_offset: FlagEnum) -> bool:
        """
        Sets flags for a guild. They are stored as Bitfields. The flags are stored in the following order:
        0: NSFW (nsfwcog.py) - NSFW commands
        1: IMAGES (imagecog.py) - Image commands
        3: WELCOME COUNTING (welcomecog.py) - Welcome Counting
        4: UWUIFICATION (uwucog.py) - uwuify
        5: LINK DETRACKING (detrack.py) - detracking
        6: MUSIC (musiccog.py) - music commands
        7: CACHING
        8: WELCOME MESSAGE
        9: MODERATION
        10: STARBOARD (Disable-Flag, 1 = Disabled 0 = Enabled)
        """
        if not gid:
            raise InvalidGuildException
        
        if isinstance(gid, int):
            guild_id = gid
        elif isinstance(gid, Guild):
            guild_id = gid.id        

        current = await RedisFlags.get_guild_flag(redis, gid, flag_offset.value)
        await redis.setbit(f"flags:{guild_id}", flag_offset, int(not current))
        return not current
#endregion
