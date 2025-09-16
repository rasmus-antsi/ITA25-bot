#!/usr/bin/env python3
"""
Debug version of the Discord bot
"""

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

print(f"🔍 Debug Info:")
print(f"  - Token loaded: {'Yes' if TOKEN else 'No'}")
print(f"  - Token length: {len(TOKEN) if TOKEN else 0}")
print(f"  - Current directory: {os.getcwd()}")

if not TOKEN:
    print("❌ No Discord token found in .env file")
    print("   Make sure you have a .env file with DISCORD_TOKEN=your_token_here")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")
    print(f"   Bot ID: {bot.user.id}")
    print(f"   Guilds: {len(bot.guilds)}")

@bot.event
async def on_command_error(ctx, error):
    print(f"❌ Command error: {error}")
    await ctx.send(f"❌ Error: {error}")

@bot.command()
async def hello(ctx):
    print(f"📝 Hello command used by {ctx.author}")
    await ctx.send("Hello! I'm alive inside Docker 🐳")

@bot.command()
async def debug(ctx):
    """Debug command to test basic functionality"""
    print(f"📝 Debug command used by {ctx.author}")
    await ctx.send("🔍 Debug: Bot is working!")

@bot.command()
async def test_scraper(ctx):
    """Test the scraper without Discord formatting"""
    print(f"📝 Test scraper command used by {ctx.author}")
    try:
        await ctx.send("🔍 Testing scraper...")
        
        # Import here to catch any import errors
        from scraper import scrape_timetable
        
        result = scrape_timetable()
        
        if result['success']:
            await ctx.send(f"✅ Scraper works! Found {result['total_events']} events")
            await ctx.send(f"📅 Week: {result['week_range']}")
            
            # Show first few lessons
            for day, lessons in list(result['lessons'].items())[:2]:
                if lessons:
                    await ctx.send(f"**{day}:** {len(lessons)} lessons")
                    for lesson in lessons[:2]:  # Show first 2 lessons
                        await ctx.send(f"  {lesson['time']} - {lesson['subject']}")
        else:
            await ctx.send(f"❌ Scraper error: {result['error']}")
        
    except Exception as e:
        print(f"❌ Scraper test error: {e}")
        await ctx.send(f"❌ Scraper test error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting debug bot...")
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Bot startup error: {e}")
