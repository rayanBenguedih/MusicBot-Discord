import discord
from discord.ext import commands
import asyncio
import os

class helper_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_message = """
        ```
        General Commands:
        _help - Displays this message
        _leave - Leaves the voice channel
        _pause - Pauses the music
        _play - Plays the music
        _queue - Displays the queue
        _resume - Resumes the music
        _skip - Skips the music
        _clear - Clears the queue
        _loop - Adds a music to be looped
        ```
        """
        self.text_channel = []
        self.TTS_USER_ID = 456205110364733470  # Replace with the specific user's Discord ID
        self.voice_channel = None
        self.tts_queue = asyncio.Queue()
        self.vc = None
        self.tts_task = None
    
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name == "bot":
                    self.text_channel.append(channel)
        await self.send_to_all(self.help_message)

    async def send_to_all(self, message):
        for channel in self.text_channel:
            await channel.send(message)

    @commands.command(name='help', help='This command displays the help message')
    async def help(self, ctx, *args):
        await ctx.send(self.help_message)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Only queue TTS if it's a DM from the specific user
        if message.author.id == self.TTS_USER_ID and isinstance(message.channel, discord.DMChannel):
            await self.tts_queue.put(message.content)
            if not self.tts_task or self.tts_task.done():
                self.tts_task = asyncio.create_task(self.process_tts_queue())

    async def process_tts_queue(self):
        # Process all queued messages
        while not self.tts_queue.empty():
            # Find or create a voice channel to speak in
            if not self.voice_channel:
                for guild in self.bot.guilds:
                    for vc in guild.voice_channels:
                        if vc.members:
                            self.voice_channel = vc
                            break

            if not self.voice_channel:
                return  # No available voice channel to join

            if not self.vc or not self.vc.is_connected():
                self.vc = await self.voice_channel.connect()
                while not self.vc.is_connected():
                    await asyncio.sleep(5)

            # Grab the next TTS message
            text = await self.tts_queue.get()

            # --- Use SylvanasVoiceCog to generate the audio ---
            voice_cog = self.bot.get_cog("VoiceCog")
            if not voice_cog:
                print("VoiceCog not found. Check that it's loaded and spelled correctly.")
                return

            # Synthesize the text to a WAV file
            output_file = voice_cog.synthesize_to_file(text, "tts_output.wav")
            if not output_file:
                print("No TTS model is loaded in VoiceCog.")
                return

            # Play the generated file
            self.vc.play(discord.FFmpegPCMAudio(output_file), after=lambda e: None)
            while self.vc.is_playing():
                await asyncio.sleep(1)

            # Clean up
            os.remove(output_file)

            # Check if the voice channel is empty
            if not self.voice_channel.members:
                await self.vc.disconnect()
                self.vc = None
                self.voice_channel = None
                break

    @commands.command(name='set_tts_channel', help='Set the voice channel for TTS')
    async def set_tts_channel(self, ctx, channel: discord.VoiceChannel):
        self.voice_channel = channel
        await ctx.send(f"TTS channel set to {channel.name}")
