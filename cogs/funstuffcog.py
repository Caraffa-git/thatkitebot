import discord, asyncio
import  random
import os, re
import requests
import markovify
from bf.util import errormsg
from bf.yamler import Tomler
from bf import url
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageColor
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import typing
from io import BytesIO

class fun_stuff(commands.Cog):
    def __init__(self, bot, dirname):
        self.bot=bot
        self._last_member=None
        self.dirname=dirname
        #Variables for markov game
        self.mgame_id=None
        self.mgame_tries=None
        self.mgame_name=None
        
    @commands.command()
    async def inspirobot(self, ctx):
        payload={"generate": "true"}
        r=requests.get("http://inspirobot.me/api", params=payload)
        embed=discord.Embed(title="A motivating quote from InspiroBot")
        embed.color=0x33cc33
        embed.set_image(url=r.text)
        await ctx.send(embed=embed)

    async def mark(self,ctx,user,old:int=200,new:int=200,leng:int=5,leng2:int=20,mode:str="long"):
        # some general variables
        guild=ctx.guild
        author: discord.User=ctx.message.author
        message:discord.Message = ctx.message
        # change the bot's status to "do not disturb" and set its game
        await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game("processing . . ."))
        # this code is used to
        is_user=False
        is_channel=False
        user_mentions = message.mentions
        channel_mentions = message.channel_mentions
        if len(user_mentions) > 0:
            # set :chan: to the first user mentioned
            chan = user_mentions[0] 
            is_user = True 
        elif len(user_mentions) == 0 and len(channel_mentions) > 0:
            # set :chan: to the first channel mentioned
            chan = channel_mentions[0]
            is_channel = True
        else:
            rest=re.findall("(\d+)", user)
            if len(rest) > 0 and not is_channel: 
                is_user=True
                # set :chan: to the user mentioned by id
                chan=self.bot.get_user(int(rest[0]))
            else:
                chan=ctx.message.author # set :chan: to the user who issued the command
                is_channel=True 

        # The variable :chan: tells the message fetcher which user's / channel's
        # messages to fetch. The :is_user: / :is_channel: tell it the type.
        # Only the first user / channel is used

        messages=[]
        if is_user and not is_channel:
            for channel in guild.text_channels:
                # add :old: messages of the user :chan: to the list :messages: (from every channel of the guild)
                async for message in channel.history(limit=old,oldest_first=True).filter(lambda m: m.author == chan):
                    messages.append(str(message.content))

                # add :new: messages of the user :chan: to the list :messages:
                async for message in channel.history(limit=new).filter(lambda m: m.author == chan):
                    messages.append(str(message.content))  
        else:
            # add :old: messages :chan: to the list :messages:           
            async for message in chan.history(limit=old, oldest_first=True):
                messages.append(str(message.content))
            # add :new: messages :chan: to the list :messages: 
            async for message in chan.history(limit=new):
                messages.append(str(message.content))
        # generate a model based on the messages in :messages:
        model=markovify.NewlineText("\n".join(messages))
        generated_list=[]
        # generate :leng: sentences
        for i in range(leng):
            if mode == "long":
                generated=model.make_sentence()
            else:
                generated=model.make_short_sentence(leng2)
            # only add sentences that are not None to :generated_list:
            if generated is not None: generated_list.append(generated)
        return generated_list, chan 

    @commands.command()
    async def markov(self,ctx,user=None,old:int=100,new:int=100,leng:int=5):
        author: discord.User=ctx.message.author
        try: 
            with ctx.channel.typing():
                if user is not None:
                    generated_list, chan=await self.mark(ctx, user, old, new, leng)
                else:
                     generated_list, chan=await self.mark(ctx, "asdasdasd", old, new, leng)
                if len(generated_list) > 0:
                    embed=discord.Embed(title="**Markov Chain Output: **", description=f"*{'. '.join(generated_list)}*")
                    embed.color=0x6E3513
                    embed.set_footer(icon_url=author.avatar_url, text=f"generated by {author}  the target was: {chan} settings: {old}o, {new}n")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(ctx, "an error has occured. I could not fetch enough messages!")
        except Exception as exc:
            print(exc)
            await errormsg(ctx, str(exc))
        finally:
            await self.bot.change_presence(status=discord.Status.online, activity=None)

    def markov_clear(self):
        self.mgame_id=None
        self.mgame_tries=None
        self.mgame_name=None   

    @commands.group()
    async def mgame(self, ctx):
        pass

    @mgame.command()
    async def start(self, ctx, tries: int):
        guild: discord.Guild=ctx.guild
        memberlist=[]
        async for member in guild.fetch_members():
            memberlist.append(member)
        the_chosen_one=random.choice(memberlist)
        print(the_chosen_one.id)
        self.mgame_id=the_chosen_one.id
        self.mgame_tries=tries
        self.mgame_name=the_chosen_one.name
        messages=[]
        try:
            generated_list, chan=await self.mark(ctx, str(the_chosen_one.id), 1000, 1000)
            if len(generated_list) > 0:
                embed=discord.Embed(title="**Who could have said this?**", description=f"*{'. '.join(generated_list)}*")
                await ctx.send(embed=embed)

        except Exception as exc:
            print(exc)
            await errormsg(ctx, "Could not fetch enough messages! Please change the parameters and try again!")
            self.markov_clear()

        finally:
            await self.bot.change_presence(status=discord.Status.online, activity=None)

    @mgame.command()
    async def guess(self, ctx, user):
        rest=re.findall("(\d+)", user)
        guild: discord.Guild=ctx.guild
        if len(rest) > 0:
            chan=int(rest[0])
        else: chan=0
        chun=re.findall(f"{user.lower()}", self.mgame_name.lower())
        if self.mgame_id is not None and self.mgame_tries is not None:
            if chan == self.mgame_id or len(chun) != 0 and self.mgame_tries != 0:
                await ctx.send("YOU ARE RIGHT! Here's a cookie for you: 🍪")
                self.markov_clear()
            else:
                self.mgame_tries -= 1
                if self.mgame_tries == 0 or self.mgame_tries < 0:
                    await errormsg(ctx, f"Sorry but that was the wrong answer. You have lost. The right answer would have been: {self.mgame_name}")
                    self.markov_clear()
                else:
                    await ctx.send(f"Sorry, that was wrong, you now have only {self.mgame_tries} tries left ")
        else:
            await errormsg(ctx, "You cannot guess, if you you havn't started a game")

    @mgame.command()
    async def stop(self, ctx):
        self.markov_clear()
    
    @commands.command()
    async def fakeword(self, ctx):
        with ctx.channel.typing():
            with ThreadPoolExecutor() as executor:
                future = executor.submit(url.word,embedmode=True)
        await ctx.send(embed=future.result())

    @commands.command()
    async def vision(self,ctx):
        await ctx.send("https://media.discordapp.net/attachments/401372087349936139/566665541465669642/vision.gif")