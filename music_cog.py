import discord
from discord.ext import commands

import logging
import json

import os

from yt_dlp import YoutubeDL

# https://pypi.org/project/youtube_dl/
# from youtube_dl import YoutubeDL


from queue import Queue, Empty

from dataclasses import dataclass

from pathlib import Path

import asyncio

@dataclass
class song_request:
    url: str
    title: str
    path: str
    duration: int
    looped: bool
    channel: discord.VoiceChannel=None
    task: asyncio.Task=None
    ctx: discord.ext.commands.Context=None

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.ext.commands.Bot = bot

        self.currentSong = ""

        self.searching: bool = False
        self.playing: bool = False
        self.paused: bool = False

        self.music_queue: Queue = Queue()
        self.request_queue: list[tuple[int, str]] = []

#'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        self.YDL_OPTIONS = {
                            'format': 'bestaudio', 
                            'noplaylist': 'True', 
                            'outtmpl': 'musics/%(id)s.%(ext)s'}

        (ffmpeg_path),*_ = filter(lambda x: 'ffmpeg' in x, os.environ['PATH'].split(';'))

        self.FFMPEG_OPTIONS = {
            
            'options': '-vn',
            'executable': str((Path(ffmpeg_path) / 'ffmpeg.exe').resolve()),
            }

        self.vc = None


    async def download_request(self, request: song_request):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                if (Path(request.path).exists()):
                    return True
                vid = ydl.download(request.url)
            except Exception:
                return False
        return True
        # download from url

    async def search_yt(self, item: str,
                        ctx: discord.ext.commands.Context,
                        voice_channel: discord.VoiceChannel,
                        looped: bool=False) -> song_request:
        self.searching =  True
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(item, download=False)
            #    with open('info.json', 'w') as f:
            #        json.dump(ydl.sanitize_info(info), f, indent=4)
            except Exception:
                self.searching = False
                return False
        request = song_request(info['original_url'],
                               info['title'],
                               f"musics/{info['id']}.{info['ext']}",
                               info['duration'],
                               looped
                               )
        request.task = asyncio.create_task(self.download_request(request))
        loop = asyncio.get_event_loop()

        self.request_queue.append((int(loop.time() * 1000), request.title))
        self.music_queue.put(request)

        request.channel = voice_channel
        request.ctx = ctx

        if request is False:
            await ctx.send("Could not download the song. Incorrect format try another keyword.")
        else:
            await ctx.send("Song Added!")

        self.searching = False
        return request
    #   return {'source': info['formats'][0]['url'], 'title': info['title']}


    async def play_next(self):

        def _recur():
            asyncio.create_task(self.play_next())

        try:
            request: song_request = self.music_queue.get_nowait()
            self.currentSong = request.title
            for i, (_, title) in enumerate(self.request_queue):
                if request.title == title:
                    break
            else:
                raise ValueError('Not in queue')
            
            self.request_queue.pop(i)

            if request.looped:
                self.music_queue.put(request)
                self.request_queue.append((int(asyncio.get_event_loop().time() * 1000), title))


            if self.vc == None or not self.vc.is_connected():
                self.vc = await request.channel.connect()
                if self.vc == None:
                    await request.ctx.send("Failed to connect to the voice channel")
                    return
            else:
                await self.vc.move_to(request.channel)
            if not request.task.done:
                await request.task

            self.playing = True
            self.vc.play(discord.FFmpegPCMAudio(source=request.path, **self.FFMPEG_OPTIONS), after=lambda e: _recur) ## Should call after, needs to skip to play next
            asyncio.get_event_loop().call_later(
                request.duration + 2,
                _recur
            )

        except Empty:
            self.playing = False
            for i in Path('musics/').glob('*'):
                i.unlink()
            


    @commands.command(name='play', aliases=["p", "playing"], help='This command plays songs')
    async def play(self, ctx, *args):
        print("PLAYCALLED")
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel

        if voice_channel is None:
            await ctx.send("Connect to a voice channel!")
        elif self.paused:
            self.vc.resume()
        else:
                                    ### Puts the song in hold when played Architecture is wrong
            await self.search_yt(query, ctx, voice_channel)
            if self.playing == False and self.searching == False:
                await self.play_next()

    @commands.command(name='loop', aliases=["l", "looping"], help='This command plays songs')
    async def loop(self, ctx, *args):
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel

        if voice_channel is None:
            await ctx.send("Connect to a voice channel!")
        elif self.paused:
            self.vc.resume()
        else:
            await self.search_yt(query, ctx, voice_channel, looped=True)
            if self.playing == False and self.searching == False:
                await self.play_next()

    @commands.command(name='pause', help='This command pauses the song')
    async def pause(self, ctx, *args):
        if self.vc == None or not self.vc.is_connected():
            await ctx.send("I am not currently playing anything!")
        elif self.vc.paused():
            await ctx.send("The song is already paused!")
        else:
            self.paused= True
            self.playing = False
            self.vc.pause()
            await ctx.send("Song paused!")


    @commands.command(name='resume', help='This command resumes the song!')
    async def resume(self, ctx, *args):
        if self.vc == None or not self.vc.is_connected():
            await ctx.send("I am not currently playing anything!")
        elif not self.vc.paused():
            await ctx.send("The song is already playing!")
        else:
            self.paused= False
            self.playing = True
            self.vc.resume()
            await ctx.send("Song resumed!")

    @commands.command(name='skip', help='This command skips the song!')
    async def skip(self, ctx, *args):
        if self.vc == None or not self.vc.is_connected():
            await ctx.send("I am not currently playing anything!")
        else:
            self.vc.stop()
            await self.play_next()

    @commands.command(name='queue', help='This command shows the songs in the queue')
    async def queue(self, ctx, *args):
        reveal = "Currently: " + self.currentSong + "\n"
        query_list = sorted(self.request_queue, key=lambda x: x[0])
        for i in query_list:
            reveal += f'{i[1]}\n'

        if reveal != "":
            await ctx.send(reveal)
        else:
            await ctx.send("No songs in queue")

    @commands.command(name="clear", help="This command clears the queue")
    async def clear(self, ctx, *args):
        if self.vc != None and self.vc.is_connected():
            self.vc.stop()
        self.music_queue = []
        await ctx.send("The queue has been cleared!")
    
    @commands.command(name="leave", help="This command stops makes the bot leave the voice channel")
    async def leave(self, ctx, *args):
        self.playing = False
        self.paused= False
        self.music_queue = []
        await self.vc.disconnect()