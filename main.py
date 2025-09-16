import os
import discord
from discord.ext import commands

TOKEN = "MTQxNTIxNTYxMzQyODYyOTUyNA.GAl9Bs.l_-yEylKcZm3g6lsn7Jn6VxwB5Wp0SrJ2l89f4"

# You must define intents now
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! I'm alive inside Docker 🐳")

bot.run(TOKEN)
