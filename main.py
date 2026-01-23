import os
import discord
import asyncio
import re
from discord.ext import commands, tasks
from dotenv import load_dotenv
from src.commands import setup_info_commands, init_database
from src.database import db
from src.scraper import VOCOScraper
from datetime import datetime, time

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    # Initialize database
    await init_database()
    # Start the daily lesson task
    daily_lessons.start()

@tasks.loop(time=time(3, 0))  # 6:00 AM every day
async def daily_lessons():
    """Send daily lessons to all servers (ITA25 only)"""
    # Check if it's a weekday (Monday=0, Sunday=6)
    if datetime.now().weekday() >= 5:  # Saturday or Sunday
        return
    
    try:
        # Get all servers with tunniplaan channels
        _, tunniplaan_channels = await db.get_channels()
        
        # Process each server
        for guild_id, channel_id in tunniplaan_channels.items():
            try:
                # Get the channel
                channel = bot.get_channel(channel_id)
                if not channel:
                    print(f"⚠️ Channel {channel_id} not found for guild {guild_id}")
                    continue
                
                # Get lessons for ITA25
                scraper = VOCOScraper()
                lessons = scraper.get_todays_lessons()
                
                if not lessons:
                    message = "📅 **Täna tunde ei ole** - Vaba päev! 🎉"
                    await channel.send(message)
                    print(f"📅 Daily lessons (no lessons) sent to {channel.guild.name}#{channel.name}")
                else:
                    # Sort lessons by time
                    lessons.sort(key=lambda x: x.get('start_time', ''))
                    
                    # Create embed
                    embed = discord.Embed(
                        title="📅 Tänased tunnid (ITA25) - Automaatne",
                        color=0x00ff00,
                        timestamp=datetime.now()
                    )
                    
                    # Add lessons to embed (same logic as manual command)
                    for i, lesson in enumerate(lessons):
                        time_str = f"{lesson.get('start_time', '')}-{lesson.get('end_time', '')}"
                        lesson_info = ""
                        
                        # Handle multiple subjects/teachers/rooms (grouped by time)
                        if 'teachers' in lesson and 'rooms' in lesson and 'subjects' in lesson:
                            # Multiple subjects/teachers/rooms (grouped by time slot)
                            teachers = lesson['teachers']
                            rooms = lesson['rooms']
                            subjects = lesson['subjects']
                            
                            for j, (teacher, room, subject) in enumerate(zip(teachers, rooms, subjects)):
                                # Clean subject name for display
                                clean_subject = re.sub(r'_\s*Rühm\s*\d+|_\s*R\d+', '', subject).strip()
                                clean_subject = re.sub(r'\s*Rühm\s*\d+|\s*R\d+', '', clean_subject).strip()
                                clean_subject = re.sub(r'_\s*$', '', clean_subject).strip()
                                
                                lesson_info += f"**{clean_subject}**\n"
                                
                                # Show group info if present
                                group_suffix = re.search(r'_\s*Rühm\s*\d+|_\s*R\d+', subject)
                                if group_suffix:
                                    lesson_info += f"📚 {group_suffix.group(0).replace('_', ' ').strip()}: "
                                elif 'Rühm' in subject or 'R1' in subject or 'R2' in subject:
                                    # Extract group info from subject name
                                    group_match = re.search(r'(Rühm\s*\d+|R\d+)', subject)
                                    if group_match:
                                        lesson_info += f"📚 {group_match.group(0)}: "
                                
                                if teacher and teacher != 'Tundmatu':
                                    lesson_info += f"👨‍🏫 {teacher}"
                                if room and room != 'Tundmatu ruum':
                                    lesson_info += f" - 🏫 {room}"
                                if j < len(teachers) - 1:
                                    lesson_info += "\n\n"
                        else:
                            # Single subject/teacher/room (original format)
                            subject = lesson.get('subject', 'Tundmatu aine')
                            clean_subject = re.sub(r'_\s*Rühm\s*\d+|_\s*R\d+', '', subject).strip()
                            clean_subject = re.sub(r'\s*Rühm\s*\d+|\s*R\d+', '', clean_subject).strip()
                            clean_subject = re.sub(r'_\s*$', '', clean_subject).strip()
                            
                            lesson_info += f"**{clean_subject}**\n"
                            
                            teacher = lesson.get('teacher', 'Tundmatu')
                            room = lesson.get('room', 'Tundmatu ruum')
                            if teacher and teacher != 'Tundmatu':
                                lesson_info += f"👨‍🏫 {teacher}"
                            if room and room != 'Tundmatu ruum':
                                lesson_info += f" - 🏫 {room}"
                        
                        embed.add_field(
                            name=f"Tund {i+1} - ⏰ {time_str}",
                            value=lesson_info,
                            inline=False
                        )
                    
                    embed.set_footer(text=f"Kokku {len(lessons)} tundi")
                    await channel.send(embed=embed)
                    print(f"📅 Daily lessons sent to {channel.guild.name}#{channel.name} (ITA25)")
                    
            except Exception as e:
                print(f"⚠️ Error sending to guild {guild_id}: {e}")
                
    except Exception as e:
        print(f"⚠️ Error in daily lessons task: {e}")

# Setup command groups
setup_info_commands(bot)

# Run the bot
bot.run(TOKEN)
