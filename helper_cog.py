import discord
from discord.ext import commands

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