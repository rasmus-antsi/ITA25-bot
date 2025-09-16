import os
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
from datetime import datetime
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
async def tunniplaan(ctx):
    try:
        # Fetch the timetable page
        url = "https://voco.ee/tunniplaan/?course=2078"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Find lessons for today
        today = datetime.now().strftime("%A")  # e.g., 'Monday'
        
        # You need to inspect the page to get correct selector
        # Example: assume lessons are in <div class="lesson" data-day="Monday">
        lessons = soup.find_all("div", {"data-day": today})

        if not lessons:
            await ctx.send(f"No lessons found for {today} 😢")
            return

        msg = f"📚 Lessons for {today}:\n"
        for lesson in lessons:
            time = lesson.get("data-time", "unknown time")
            subject = lesson.get_text(strip=True)
            msg += f"- {time}: {subject}\n"

        await ctx.send(msg)

    except Exception as e:
        await ctx.send(f"❌ Could not fetch timetable: {e}")

bot.run(TOKEN)
