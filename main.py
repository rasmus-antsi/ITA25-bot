import os
import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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

@bot.command()
async def debug_scraper(ctx):
    """Debug command to see what the scraper finds"""
    try:
        await ctx.send("🔍 Debugging scraper...")
        
        result = scrape_timetable()
        
        if not result['success']:
            await ctx.send(f"❌ Error: {result['error']}")
            return
        
        lessons = result['lessons']
        
        debug_msg = f"**Debug Info:**\n"
        debug_msg += f"Found {len(lessons)} lessons\n\n"
        
        for i, lesson in enumerate(lessons, 1):
            debug_msg += f"**{i}.** {lesson['time']}\n"
            debug_msg += f"   Subject: {lesson['subject']}\n"
            debug_msg += f"   Room: {lesson['room']}\n"
            debug_msg += f"   Teacher: {lesson['teacher']}\n\n"
        
        # Split message if too long
        if len(debug_msg) > 2000:
            debug_msg = debug_msg[:1900] + "...\n(truncated)"
        
        await ctx.send(debug_msg)
        
    except Exception as e:
        await ctx.send(f"❌ Debug error: {str(e)}")

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
            
            # Wait for the page to load and course selector to appear
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.ID, "course_select")))
            
            # Wait for course options to be populated
            time.sleep(3)
            
            # Select the course (2078)
            try:
                course_select = driver.find_element(By.ID, "course_select")
                course_select.click()
                time.sleep(1)
                
                # Look for the course option with value 2078
                course_option = driver.find_element(By.CSS_SELECTOR, "option[value='2078']")
                course_option.click()
                time.sleep(2)
                
                # Wait for calendar to load
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "fc")))
                time.sleep(3)  # Additional wait for events to load
                
            except Exception as e:
                print(f"Error selecting course: {e}")
                # Continue anyway, maybe the course is already selected
            
            # Get today's date
            today = datetime.now()
            today_weekday = today.weekday()  # 0=Monday, 1=Tuesday, etc.
            
            # Get all events from the calendar - try multiple selectors
            all_events = []
            event_selectors = [
                ".fc-event",
                ".fc-event-container .fc-event", 
                ".fc-content .fc-event",
                "[class*='fc-event']"
            ]
            
            for selector in event_selectors:
                events = driver.find_elements(By.CSS_SELECTOR, selector)
                if events:
                    all_events = events
                    print(f"Found {len(events)} events using selector: {selector}")
                    break
            
            if not all_events:
                print("No events found with any selector")
                # Try to get page source for debugging
                page_source = driver.page_source
                if "fc-event" in page_source:
                    print("fc-event found in page source but not as elements")
                else:
                    print("fc-event not found in page source")
            
            # Find today's events by looking at the calendar structure more carefully
            today_events = []
            
            # Get today's date in the format used by the calendar
            today = datetime.now()
            today_str = today.strftime("%d.%m")  # e.g., "16.9"
            today_weekday = today.strftime("%a")  # e.g., "Tue"
            
            print(f"Looking for today's events: {today_weekday} {today_str}")
            
            # Find today's column by looking at day headers
            day_headers = driver.find_elements(By.CSS_SELECTOR, "th[class*='fc-day']")
            today_column_index = None
            
            # Try multiple ways to identify today's column
            for i, header in enumerate(day_headers):
                header_text = header.text
                header_class = header.get_attribute("class")
                print(f"Header {i}: '{header_text}' class: '{header_class}'")
                
                # Look for today's date in various formats
                today_formats = [
                    today_str,  # "16.9"
                    today.strftime("%d.%m"),  # "16.09"
                    today.strftime("%d"),  # "16"
                    today.strftime("%a"),  # "Tue"
                    today.strftime("%A"),  # "Tuesday"
                ]
                
                # Check if any format matches
                for fmt in today_formats:
                    if fmt in header_text or "fc-today" in header_class:
                        today_column_index = i
                        print(f"Found today's column at index {i} using format '{fmt}'")
                        break
                
                if today_column_index is not None:
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
                            print(f"Found {len(cell_events)} events in today's cell")
                except Exception as e:
                    print(f"Error finding events in today's column: {e}")
            else:
                print("Could not find today's column")
            
            # If no events found, try a different approach
            if len(today_events) == 0:
                print("No events found in today's column, trying fallback approach")
                
                # Since we can't find today's column precisely, we'll use a different strategy
                # Look for events that have data attributes indicating they're for today
                for event in all_events:
                    try:
                        # Check if this event has a data-start attribute that matches today
                        event_start = event.get_attribute("data-start")
                        if event_start:
                            # Parse the date from data-start attribute
                            try:
                                # FullCalendar uses ISO format: 2025-09-16T08:30:00
                                event_date = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                                if event_date.date() == today.date():
                                    today_events.append(event)
                                    print(f"Added event for today: {event.text[:50]}...")
                                    continue
                                else:
                                    print(f"Skipping event from {event_date.date()}: {event.text[:50]}...")
                                    continue
                            except Exception as e:
                                print(f"Error parsing date {event_start}: {e}")
                                pass
                        
                        # If no data-start attribute, be more conservative
                        # Only include events that we're confident are for today
                        event_text = event.text
                        if event_text and event_text.strip():
                            # Skip events that are clearly from other days
                            skip_patterns = [
                                'Tegevuspäev',  # Activity day events
                                'Sissejuhatus IT-valdkonda_Rühm 1',  # This is typically Monday
                                'Kultuur ja suhtlemine',  # This seems to be from another day
                            ]
                            
                            should_skip = False
                            for pattern in skip_patterns:
                                if pattern in event_text:
                                    should_skip = True
                                    print(f"Skipping event with pattern '{pattern}': {event_text[:50]}...")
                                    break
                            
                            if not should_skip:
                                # Only include if it looks like a typical lesson
                                if any(keyword in event_text.lower() for keyword in [
                                    'digitehnoloogia', 'oskused', 'üldainete', 'programmeerimise'
                                ]):
                                    today_events.append(event)
                                    print(f"Added event (fallback): {event_text[:50]}...")
                                else:
                                    print(f"Skipping uncertain event: {event_text[:50]}...")
                                
                    except Exception as e:
                        print(f"Error processing event: {e}")
                        continue
                
                # If still no events, show a message that there are no lessons today
                if len(today_events) == 0:
                    print("No events found for today")
                    today_events = []
            
            # If we still have too many events, try to limit to a reasonable number
            # This is a safety measure to avoid showing too many lessons
            if len(today_events) > 10:
                print(f"Found {len(today_events)} events, limiting to first 10")
                today_events = today_events[:10]
            
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
                        r'Kopli A',           # Just "Kopli A" without room number
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

def scrape_weekly_timetable():
    """Scrape the entire week's timetable from voco.ee using Selenium"""
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
            
            # Wait for the page to load and course selector to appear
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.ID, "course_select")))
            
            # Wait for course options to be populated
            time.sleep(3)
            
            # Select the course (2078)
            try:
                course_select = driver.find_element(By.ID, "course_select")
                course_select.click()
                time.sleep(1)
                
                # Look for the course option with value 2078
                course_option = driver.find_element(By.CSS_SELECTOR, "option[value='2078']")
                course_option.click()
                time.sleep(2)
                
                # Wait for calendar to load
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "fc")))
                time.sleep(3)  # Additional wait for events to load
                
            except Exception as e:
                print(f"Error selecting course: {e}")
                # Continue anyway, maybe the course is already selected
            
            # Get all events from the calendar
            all_events = []
            event_selectors = [
                ".fc-event",
                ".fc-event-container .fc-event", 
                ".fc-content .fc-event",
                "[class*='fc-event']"
            ]
            
            for selector in event_selectors:
                events = driver.find_elements(By.CSS_SELECTOR, selector)
                if events:
                    all_events = events
                    print(f"Found {len(events)} events using selector: {selector}")
                    break
            
            if not all_events:
                print("No events found with any selector")
                return {'success': False, 'error': 'No events found in calendar'}
            
            # Parse events into lessons grouped by day
            weekly_lessons = {}
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for event in all_events:
                try:
                    # Get event details
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
                    
                    # Try to get the day from data-start attribute
                    event_start = event.get_attribute("data-start")
                    day_name = "Unknown Day"
                    
                    if event_start:
                        try:
                            # Handle different date formats
                            if 'T' in event_start:
                                # ISO format: 2025-09-16T08:30:00
                                event_date = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                            else:
                                # Date only format: 2025-09-16
                                event_date = datetime.fromisoformat(event_start)
                            
                            day_name = day_names[event_date.weekday()]
                            print(f"Event '{title[:30]}...' assigned to {day_name} (from {event_start})")
                        except Exception as e:
                            print(f"Error parsing date '{event_start}': {e}")
                            pass
                    else:
                        print(f"No data-start attribute for event: '{title[:30]}...'")
                        # Try to determine day by looking at the event's position
                        try:
                            # Get the event's parent elements to find which day column it's in
                            parent = event.find_element(By.XPATH, "./ancestor::td[contains(@class, 'fc-day')]")
                            if parent:
                                # Look for day information in the parent's class or nearby elements
                                parent_class = parent.get_attribute("class")
                                print(f"Event parent class: {parent_class}")
                                
                                # Try to find day header for this column
                                day_headers = driver.find_elements(By.CSS_SELECTOR, "th[class*='fc-day']")
                                for i, header in enumerate(day_headers):
                                    if f"fc-day-{i}" in parent_class or f"fc-day{i}" in parent_class:
                                        header_text = header.text
                                        if header_text:
                                            # Try to extract day from header text
                                            for day in day_names:
                                                if day.lower()[:3] in header_text.lower():
                                                    day_name = day
                                                    print(f"Event assigned to {day_name} based on position")
                                                    break
                                        break
                        except Exception as e:
                            print(f"Could not determine day by position: {e}")
                    
                    # Parse the event data
                    room = ""
                    teacher = ""
                    subject = title
                    
                    # Extract room number
                    room_patterns = [
                        r'Kopli A - (A\d+)',  # Kopli A - A401
                        r'\(A\d+\)',          # (A401)
                        r'A\d+',              # A401
                        r'Kopli A',           # Just "Kopli A" without room number
                    ]
                    
                    for pattern in room_patterns:
                        room_match = re.search(pattern, title)
                        if room_match:
                            room = room_match.group(1) if room_match.groups() else room_match.group(0)
                            break
                    
                    # Extract teacher names
                    teacher_patterns = [
                        r'([A-Z][a-z]+ [A-Z][a-z]+)',  # First Last
                        r'([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+)',  # First Middle Last
                    ]
                    
                    for pattern in teacher_patterns:
                        teacher_match = re.search(pattern, title)
                        if teacher_match:
                            teacher = teacher_match.group(1)
                            break
                    
                    # Clean up subject name
                    subject = re.sub(r'Kopli A.*', '', subject).strip()
                    subject = re.sub(r'\([^)]*\)', '', subject).strip()
                    subject = re.sub(r'[A-Z][a-z]+ [A-Z][a-z]+.*', '', subject).strip()
                    subject = re.sub(r'\s+', ' ', subject).strip()
                    
                    lesson = {
                        'time': time_text,
                        'subject': subject,
                        'room': room,
                        'teacher': teacher
                    }
                    
                    # Add to weekly lessons
                    if day_name not in weekly_lessons:
                        weekly_lessons[day_name] = []
                    weekly_lessons[day_name].append(lesson)
                        
                except Exception as e:
                    print(f"Error parsing event: {e}")
                    continue
            
            # Get week range
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            week_range = f"{week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m.%Y')}"
            
            return {
                'success': True,
                'lessons': weekly_lessons,
                'week_range': week_range,
                'source': 'Live data from voco.ee'
            }
            
        finally:
            driver.quit()
            
    except Exception as e:
        return {'success': False, 'error': f'Scraping error: {str(e)}'}

@bot.command()
async def tunniplaan(ctx):
    try:
        await ctx.send("📚 Fetching this week's lessons...")
        
        result = scrape_weekly_timetable()
        
        if not result['success']:
            await ctx.send(f"❌ Error: {result['error']}")
            return
        
        weekly_lessons = result['lessons']
        source = result['source']
        
        # Create embed
        embed = discord.Embed(
            title=f"📚 This Week's Lessons - {result['week_range']}",
            color=0x00ff00
        )
        
        if weekly_lessons:
            # Group lessons by day
            for day, day_lessons in weekly_lessons.items():
                if day_lessons:
                    # Group lessons by time slot for this day
                    lessons_by_time = {}
                    for lesson in day_lessons:
                        time_slot = lesson['time']
                        if time_slot not in lessons_by_time:
                            lessons_by_time[time_slot] = []
                        lessons_by_time[time_slot].append(lesson)
                    
                    # Create day section
                    day_text = f"**{day}**\n"
                    
                    # Add lessons for each time slot
                    for time_slot, time_lessons in sorted(lessons_by_time.items()):
                        day_text += f"🕐 **{time_slot}**\n"
                        for lesson in time_lessons:
                            teacher_text = f"👨‍🏫 {lesson['teacher']}" if lesson['teacher'] else ""
                            room_text = f"📍 {lesson['room']}" if lesson['room'] else ""
                            
                            lesson_line = f"• {lesson['subject']}"
                            if room_text:
                                lesson_line += f" {room_text}"
                            if teacher_text:
                                lesson_line += f" {teacher_text}"
                            
                            day_text += f"{lesson_line}\n"
                        day_text += "\n"
                    
                    # Add day to embed (limit field length)
                    if len(day_text) > 1024:
                        day_text = day_text[:1020] + "..."
                    
                    embed.add_field(
                        name=f"📅 {day}",
                        value=day_text,
                        inline=True
                    )
        else:
            embed.add_field(
                name="No lessons this week", 
                value="Enjoy your free time! 🎉", 
                inline=False
            )
        
        embed.set_footer(text=f"Source: {source}")
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

bot.run(TOKEN)
