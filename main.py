import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! I'm alive inside Docker 🐳")

@bot.command()
async def info(ctx):
    """Send important information to the info channel"""
    # Create an embed with information
    embed = discord.Embed(
        title="📢 Important Information",
        color=0x00ff00,
        description="Please check the following information:"
    )
    
    # Add fields with information
    embed.add_field(
        name="📅 Schedule Updates",
        value="Check the timetable for any changes to your classes",
        inline=False
    )
    
    embed.add_field(
        name="📚 Assignments",
        value="Make sure to complete all pending assignments",
        inline=False
    )
    
    embed.add_field(
        name="💬 Communication",
        value="Stay updated with announcements in this channel",
        inline=False
    )
    
    embed.set_footer(text="ITA25 Bot • Stay informed!")
    
    # Send the message with @everyone ping
    await ctx.send("@everyone", embed=embed)


bot.run(TOKEN)