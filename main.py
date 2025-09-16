import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from src.commands import setup_info_commands

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# Setup command groups
setup_info_commands(bot)

# Run the bot
bot.run(TOKEN)
