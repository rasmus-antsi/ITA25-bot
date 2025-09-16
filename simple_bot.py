#!/usr/bin/env python3
"""
Minimal working Discord bot
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is ready! Logged in as {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! Bot is working! 🎉")

@bot.command()
async def test(ctx):
    await ctx.send("Test command works! ✅")

if __name__ == "__main__":
    print("🚀 Starting simple bot...")
    bot.run(TOKEN)
