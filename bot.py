import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix="$",
    intents=intents
)

@bot.event
async def on_ready():

    try:

        synced = await bot.tree.sync()

        print(
            f"Synced {len(synced)} commands."
        )

    except Exception as e:

        print(e)

    print(
        f"Logged in as {bot.user}"
    )

async def main():

    async with bot:

        await bot.load_extension(
            "cogs.loa"
        )

        await bot.load_extension(
            "cogs.leaderboard"
        )

        await bot.load_extension(
            "cogs.roster"
        )

        await bot.start(TOKEN)

asyncio.run(main())