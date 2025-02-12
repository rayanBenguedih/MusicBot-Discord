import discord
from discord.ext import commands

import asyncio


from helper_cog import helper_cog
from music_cog import music_cog

intents = discord.Intents.default()

intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='_', intents=intents)

bot.remove_command("help")

async def setup(bot):
    await bot.add_cog(helper_cog(bot))
    await bot.add_cog(music_cog(bot))

asyncio.run(setup(bot))
TOKEN = open("C:\\Users\\Canopus\\Pictures\\Apollo\\token.txt", "r").readline()

bot.run(TOKEN)