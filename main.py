import discord
from discord.ext import commands
import asyncio

from bot_cogs.helper_cog import helper_cog
from bot_cogs.music_cog import music_cog
from bot_cogs.voice_cog import VoiceCog


intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix='_', intents=intents)
bot.remove_command("help")

print("Launching Apollo...")
async def setup(bot):
    await bot.add_cog(helper_cog(bot))
    await bot.add_cog(music_cog(bot))
    await bot.add_cog(VoiceCog(bot)) 

asyncio.run(setup(bot))

TOKEN = open("C:\\Users\\Canopus\\Pictures\\Apollo\\token.txt", "r").readline()

bot.run(TOKEN)
print("Battlecruiser Operational")