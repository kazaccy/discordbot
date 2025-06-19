import discord
import datetime as dt
import pytz
import asyncio
import random
import json
import os
from discord.ext import tasks, commands
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/",intents = intents)

@bot.event
async def on_ready():
    
    synced = await bot.tree.sync()
    
    print(f"{bot.user} połączony!")
    print("📋 Zsynchronizowane komendy:")
    for cmd in synced:
        print(f" - /{cmd.name} ({cmd.description})")


async def main():
    await bot.load_extension("cogs.cwelometr")
    await bot.load_extension("cogs.papiezowa")
    await bot.load_extension("cogs.niepisanie")
    await bot.load_extension("cogs.muzyk")
    await bot.start(TOKEN)
asyncio.run(main())