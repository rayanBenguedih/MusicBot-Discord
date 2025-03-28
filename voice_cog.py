import discord
from discord.ext import commands
import asyncio
import os
from TTS.api import TTS



class VoiceCog(commands.Cog):
    def __init__(self, bot):
        
        model_dir = os.path.join(os.path.dirname(__file__), "vits_best_model")
        model_path = os.path.join(model_dir, "best_model.pth")
        config_path = os.path.join(model_dir, "config.json")

        self.bot = bot
        self.tts_model = TTS(model_path=model_path, config_path=config_path, progress_bar=False)
        self.output_file = "tts_output.wav"
        self.voice_channel = None
        self.vc = None

    async def join_voice_channel(self, ctx):
        if ctx.author.voice and ctx.author.voice.channel:
            self.voice_channel = ctx.author.voice.channel
            if not self.vc or not self.vc.is_connected():
                self.vc = await self.voice_channel.connect()
        else:
            await ctx.send("You need to be in a voice channel!")
            return False
        return True

    def synthesize_to_file(self, text, output_file):
        """Generate speech from text and save to a file."""
        self.tts_model.tts_to_file(text=text, file_path=output_file)
        return output_file

    async def play_tts(self, text):
        """Generate TTS audio and play it in a voice channel."""
        if not self.voice_channel:
            print("No voice channel set for TTS.")
            return

        # Synthesize speech
        self.synthesize_to_file(text, self.output_file)

        # Play audio in voice channel
        if self.vc and self.vc.is_connected():
            self.vc.play(discord.FFmpegPCMAudio(self.output_file), after=lambda e: None)
            while self.vc.is_playing():
                await asyncio.sleep(1)

            os.remove(self.output_file)

    @commands.command(name='say', help='Convert text to speech and play in a voice channel')
    async def say(self, ctx, *, text: str):
        if await self.join_voice_channel(ctx):
            await self.play_tts(text)

    @commands.command(name='leave_tts', help='Disconnects the bot from the voice channel')
    async def leave(self, ctx):
        if self.vc and self.vc.is_connected():
            await self.vc.disconnect()
            self.vc = None
            self.voice_channel = None
        await ctx.send("Disconnected from voice channel.")

async def setup(bot):
    await bot.add_cog(VoiceCog(bot))
