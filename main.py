import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from scraper import scrape_timetable

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
async def tunniplaan(ctx):
    """Get weekly lessons from voco.ee"""
    try:
        await ctx.send("📚 Fetching weekly lessons...")
        
        result = scrape_timetable()
        
        if not result['success']:
            await ctx.send(f"❌ Error: {result['error']}")
            return
        
        weekly_lessons = result['lessons']
        week_range = result['week_range']
        source = result['source']
        
        # Create embed
        embed = discord.Embed(
            title=f"📚 Weekly Lessons - {week_range}",
            color=0x00ff00,
            description=f"*{source}*"
        )
        
        for day, day_lessons in weekly_lessons.items():
            if day_lessons:
                # Create a clean table format
                day_text = "```\n"
                day_text += f"{'Time':<12} {'Subject':<30} {'Room':<8} {'Teacher':<20}\n"
                day_text += f"{'-'*12} {'-'*30} {'-'*8} {'-'*20}\n"
                
                for lesson in day_lessons:
                    time = lesson['time']
                    subject = lesson['subject'][:29]  # Limit subject length
                    room = lesson['room'] or "N/A"
                    teacher = lesson['teacher'][:19]  # Limit teacher length
                    day_text += f"{time:<12} {subject:<30} {room:<8} {teacher:<20}\n"
                
                day_text += "```"
                
                embed.add_field(
                    name=f"📅 {day}",
                    value=day_text,
                    inline=False
                )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error fetching lessons: {str(e)}")

bot.run(TOKEN)