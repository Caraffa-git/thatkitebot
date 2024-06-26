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
from discord import Embed

from thatkitebot.base import url
from thatkitebot.base.util import EmbedColors as ec
#endregion

#region main code
async def gen_embed(self) -> Embed:
    embed = Embed(
        color=ec.purple_violet,
        title=f"About {self.bot.user.name}",
        description=
        """
        This bot licensed under the MIT license is open source and free to use for everyone.
        I put a lot of my time into this bot and I really hope you enjoy it.
        The source code is available [here](https://github.com/ThatRedKite/thatkitebot), feel free to contribute!
        If you like it, consider [giving me a donation](https://www.buymeacoffee.com/ThatRedKite) to keep the server running.
        """
    )
    try:
        embed.set_thumbnail(url=str(self.bot.user.avatar.url))
    except:
        pass
    # dictionary for discord username lookup from GitHub username
    # format: "githubusername":"discordID"
    authordict = {
        "ThatRedKite": "<@249056455552925697>",
        "diminDDL": "<@312591385624576001>",
        "Cuprum77": "<@323502550340861963>",
        "laserpup": "<@357258808105500674>",
        "woo200": "<@1129767250342195222>",
        "Caraffa-git": "<@303227573121449994>"
    }
    jsonData = await url._contributorjson(self.bot.aiohttp_session)
    # get a list of "login" field values from json string variable jsonData
    authorlist = [x["login"] for x in jsonData]
    # if a username contains [bot] remove it from the list
    authorlist = [x for x in authorlist if not x.lower().__contains__("bot")]
    # keed only first 5 contributors in authorlist
    authorlist = authorlist[:5]
    embedStr = ""
    for i in authorlist:
        if i in authordict:
            embedStr += f"{authordict[i]}\n"
        else:
            embedStr += f"{i}\n"
    embedStr += "and other [contributors](https://github.com/ThatRedKite/thatkitebot/graphs/contributors)"
    embed.add_field(
        name="Authors",
        value=embedStr
    )
    embed.add_field(
        name="Libraries used",
        inline=False,
        value="python libraries are listed [here](https://raw.githubusercontent.com/ThatRedKite/thatkitebot/master/requirements.txt)"
    )
    embed.add_field(
        name="Powered by",
        inline=False,
        value=
        """
        [Python](https://www.python.org/) 
        [Docker](https://www.docker.com/)
        [Redis](https://redis.io/)
        """
    )

    embed.set_footer(text="ThatKiteBot v{}".format(self.bot.version))
    return embed
#endregion
