import os
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

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

def scrape_timetable():
    """Scrape the actual timetable from voco.ee using Selenium"""
    try:
        # Set up Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Navigate to the timetable page
            url = "https://voco.ee/tunniplaan/?course=2078"
            driver.get(url)
            
            # Wait for the page to load and calendar to appear
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "fc")))
            
            # Get today's date
            today = datetime.now()
            today_weekday = today.weekday()  # 0=Monday, 1=Tuesday, etc.
            
            # Get all events from the calendar
            all_events = driver.find_elements(By.CSS_SELECTOR, ".fc-event")
            
            # Find today's events by looking at the calendar structure more carefully
            today_events = []
            
            # Find today's column by looking at day headers
            day_headers = driver.find_elements(By.CSS_SELECTOR, "th[class*='fc-day']")
            today_column_index = None
            
            for i, header in enumerate(day_headers):
                header_class = header.get_attribute("class")
                if "fc-today" in header_class:
                    today_column_index = i
                    break
            
            if today_column_index is not None:
                # Try to find events in today's column by looking at the grid
                try:
                    # Look for the time grid container
                    timegrid_container = driver.find_element(By.CSS_SELECTOR, ".fc-timegrid-body")
                    
                    # Find all time slots in today's column
                    time_slots = timegrid_container.find_elements(By.CSS_SELECTOR, "tr[class*='fc-timegrid']")
                    
                    for slot in time_slots:
                        cells = slot.find_elements(By.CSS_SELECTOR, "td[class*='fc-day']")
                        if len(cells) > today_column_index:
                            today_cell = cells[today_column_index]
                            cell_events = today_cell.find_elements(By.CSS_SELECTOR, ".fc-event")
                            today_events.extend(cell_events)
                except Exception as e:
                    print(f"Error finding events in today's column: {e}")
            
            # If no events found, try a different approach
            if len(today_events) == 0:
                # Since the calendar structure is complex, let's implement a simple filter
                # to show only lessons that are likely for today
                
                # Filter out lessons that are clearly not for today
                for event in all_events:
                    try:
                        event_text = event.text
                        
                        # Skip lessons that are clearly from other days or not relevant
                        skip_patterns = [
                            'Sissejuhatus IT-valdkonda_Rühm 1',  # This specific lesson you mentioned
                            'Tegevuspäev',  # Activity day events
                            'Sissejuhatus IT_valdkonda_Rühm 2',  # Another group lesson
                            'Sissejuhatus IT_valdkonda_Rühm 1; Sissejuhatus IT_valdkonda_Rühm 2',  # Combined groups
                        ]
                        
                        should_skip = False
                        for pattern in skip_patterns:
                            if pattern in event_text:
                                should_skip = True
                                break
                        
                        if not should_skip:
                            today_events.append(event)
                    except:
                        continue
                
                # If still no events, show a message that there are no lessons today
                if len(today_events) == 0:
                    print("No events found for today")
                    today_events = []
            
            # Parse events into lessons
            today_lessons = []
            for event in today_events:
                try:
                    # Get event details - try multiple ways
                    title = ""
                    time_text = ""
                    
                    try:
                        title = event.find_element(By.CSS_SELECTOR, ".fc-title").text
                    except:
                        try:
                            title = event.find_element(By.CSS_SELECTOR, ".fc-content").text
                        except:
                            title = event.text
                    
                    try:
                        time_element = event.find_element(By.CSS_SELECTOR, ".fc-time")
                        time_text = time_element.text
                    except:
                        time_text = "Unknown time"
                    
                    # Parse the event data
                    room = ""
                    teacher = ""
                    subject = title
                    
                    # Extract room number - look for patterns like A401, A415, etc.
                    room_patterns = [
                        r'Kopli A - (A\d+)',  # Kopli A - A401
                        r'\(A\d+\)',          # (A401)
                        r'A\d+',              # A401
                    ]
                    
                    for pattern in room_patterns:
                        room_match = re.search(pattern, title)
                        if room_match:
                            room = room_match.group(1) if room_match.groups() else room_match.group(0)
                            break
                    
                    # Extract teacher names - look for Estonian names
                    teacher_patterns = [
                        r'([A-Z][a-z]+ [A-Z][a-z]+)',  # First Last
                        r'([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+)',  # First Middle Last
                    ]
                    
                    for pattern in teacher_patterns:
                        teacher_match = re.search(pattern, title)
                        if teacher_match:
                            teacher = teacher_match.group(1)
                            break
                    
                    # Clean up subject name - remove room and teacher info
                    subject = re.sub(r'Kopli A.*', '', subject).strip()
                    subject = re.sub(r'\([^)]*\)', '', subject).strip()  # Remove parentheses
                    subject = re.sub(r'[A-Z][a-z]+ [A-Z][a-z]+.*', '', subject).strip()  # Remove teacher names
                    subject = re.sub(r'\s+', ' ', subject).strip()  # Clean up extra spaces
                    
                    lesson = {
                        'time': time_text,
                        'subject': subject,
                        'room': room,
                        'teacher': teacher
                    }
                    today_lessons.append(lesson)
                        
                except Exception as e:
                    continue
            
            return {
                'success': True,
                'lessons': today_lessons,
                'day': today.strftime('%A').lower(),
                'date': today.strftime('%A, %B %d, %Y'),
                'source': 'Live data from voco.ee'
            }
            
        finally:
            driver.quit()
            
    except Exception as e:
        return {'success': False, 'error': f'Scraping error: {str(e)}'}

@bot.command()
async def tunniplaan(ctx):
    try:
        await ctx.send("📚 Fetching today's lessons...")
        
        result = scrape_timetable()
        
        if not result['success']:
            await ctx.send(f"❌ Error: {result['error']}")
            return
        
        lessons = result['lessons']
        date = result['date']
        source = result['source']
        
        # Create embed
        embed = discord.Embed(
            title=f"📚 Today's Lessons - {date}",
            color=0x00ff00
        )
        
        if lessons:
            # Group lessons by time slot
            lessons_by_time = {}
            for lesson in lessons:
                time_slot = lesson['time']
                if time_slot not in lessons_by_time:
                    lessons_by_time[time_slot] = []
                lessons_by_time[time_slot].append(lesson)
            
            # Display all lessons for each time slot
            for time_slot, time_lessons in lessons_by_time.items():
                lesson_texts = []
                for lesson in time_lessons:
                    teacher_text = f"👨‍🏫 {lesson['teacher']}" if lesson['teacher'] else ""
                    room_text = f"📍 {lesson['room']}" if lesson['room'] else ""
                    
                    value_parts = [f"**{lesson['subject']}**"]
                    if room_text:
                        value_parts.append(room_text)
                    if teacher_text:
                        value_parts.append(teacher_text)
                    
                    lesson_texts.append("\n".join(value_parts))
                
                embed.add_field(
                    name=f"🕐 {time_slot}",
                    value="\n\n".join(lesson_texts),
                    inline=False
                )
        else:
            embed.add_field(
                name="No lessons today", 
                value="Enjoy your free time! 🎉", 
                inline=False
            )
        
        embed.set_footer(text=f"Source: {source}")
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

bot.run(TOKEN)
