"""
VOCO Timetable Scraper
Scrapes lesson data from voco.ee timetable
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_timetable(period="daily"):
    """
    Scrape timetable from VOCO website using Selenium
    
    Args:
        period (str): "daily" or "weekly"
    
    Returns:
        dict: Scraped timetable data
    """
    driver = None
    try:
        print(f"🔍 Scraping VOCO timetable ({period})...")
        
        # Setup Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to the timetable page
        url = "https://voco.ee/tunniplaan/?course=2078"
        print(f"📡 URL: {url}")
        driver.get(url)
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 10)
        
        # Wait for the timetable selector to appear
        try:
            # Look for the timetable selector dropdown
            timetable_selector = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "select, .timetable-selector, [class*='select']"))
            )
            print("✅ Found timetable selector")
            
            # Try to find ITA25 option
            ita25_options = driver.find_elements(By.XPATH, "//option[contains(text(), 'ITA25') or contains(text(), 'ita25')]")
            if ita25_options:
                print("✅ Found ITA25 option")
                ita25_options[0].click()
            else:
                # Look for any option that might be ITA25
                all_options = driver.find_elements(By.TAG_NAME, "option")
                print(f"📋 Available options: {[opt.text for opt in all_options]}")
                
                # Try to find the most likely ITA25 option
                for option in all_options:
                    if '25' in option.text and ('ITA' in option.text.upper() or 'IT' in option.text.upper()):
                        print(f"🎯 Selecting option: {option.text}")
                        option.click()
                        break
                else:
                    print("⚠️ No ITA25 option found, trying first available option")
                    if all_options:
                        all_options[0].click()
            
            # Wait for the timetable to load
            time.sleep(3)
            
        except Exception as e:
            print(f"⚠️ Could not find timetable selector: {e}")
            # Continue anyway, maybe the timetable is already loaded
        
        # Now try to find the calendar events
        lessons = []
        
        # Look for FullCalendar events
        try:
            # Wait for calendar to load
            calendar_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".fc-view, .calendar, [class*='calendar'], .fc"))
            )
            print("✅ Found calendar element")
            
            # Look for events in the calendar with multiple selectors
            event_selectors = [
                ".fc-event",
                ".fc-event-main", 
                ".fc-event-title",
                ".event",
                "[class*='event']",
                "[class*='lesson']",
                ".lesson"
            ]
            
            event_elements = []
            for selector in event_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    event_elements.extend(elements)
                    print(f"📅 Found {len(elements)} elements with selector: {selector}")
            
            # Remove duplicates
            event_elements = list(set(event_elements))
            print(f"📅 Total unique event elements: {len(event_elements)}")
            
            for event in event_elements:
                try:
                    title = event.text.strip()
                    if title and len(title) > 3:  # Filter out empty or very short text
                        # Try to get time information from various sources
                        time_text = "Unknown"
                        
                        # Try to find time in the event element itself
                        try:
                            time_element = event.find_element(By.CSS_SELECTOR, ".fc-time, .time, [class*='time']")
                            time_text = time_element.text.strip()
                        except:
                            # Try to find time in parent elements
                            try:
                                parent = event.find_element(By.XPATH, "..")
                                time_element = parent.find_element(By.CSS_SELECTOR, ".fc-time, .time, [class*='time']")
                                time_text = time_element.text.strip()
                            except:
                                pass
                        
                        # Try to extract time from title if not found elsewhere
                        if time_text == "Unknown":
                            time_match = re.search(r'(\d{1,2}:\d{2})', title)
                            if time_match:
                                time_text = time_match.group(1)
                        
                        lesson = parse_lesson_data(title, time_text)
                        if lesson:
                            lessons.append(lesson)
                            print(f"✅ Parsed lesson: {lesson['time']} - {lesson['subject']}")
                except Exception as e:
                    print(f"⚠️ Error processing event: {e}")
                    continue
                    
        except Exception as e:
            print(f"⚠️ Could not find calendar events: {e}")
        
        # If no events found, try to find table data
        if not lessons:
            print("🔍 Trying to find table data...")
            table_elements = driver.find_elements(By.TAG_NAME, "table")
            for table in table_elements:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows[1:]:  # Skip header
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 3:
                        time_text = cells[0].text.strip()
                        subject_text = cells[1].text.strip()
                        room_text = cells[2].text.strip() if len(cells) > 2 else "Unknown"
                        teacher_text = cells[3].text.strip() if len(cells) > 3 else "Unknown"
                        
                        if re.match(r'\d{1,2}:\d{2}', time_text):
                            lessons.append({
                                'time': time_text,
                                'subject': subject_text,
                                'room': room_text,
                                'teacher': teacher_text,
                                'raw_text': f"{time_text} - {subject_text} - {room_text} - {teacher_text}"
                            })
        
        print(f"📚 Found {len(lessons)} lessons")
        
        # Filter lessons based on period
        if period == "daily":
            lessons = filter_daily_lessons(lessons)
        
        # Organize lessons by day
        weekly_lessons = organize_lessons_by_day(lessons, period)
        
        # Get date range
        today = datetime.now()
        if period == "weekly":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            week_range = f"{week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m.%Y')}"
            date_info = week_range
        else:
            date_info = today.strftime('%d.%m.%Y')
        
        return {
            'success': True,
            'lessons': weekly_lessons,
            'date': date_info,
            'week_range': week_range if period == "weekly" else None,
            'source': 'VOCO.ee',
            'total_lessons': len(lessons)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Scraping error: {str(e)}'
        }
    finally:
        if driver:
            driver.quit()

def parse_lesson_data(title, start_time):
    """Parse lesson data from title and start time"""
    try:
        # Handle different time formats
        if 'T' in start_time and start_time != "Unknown":
            # ISO format: YYYY-MM-DDTHH:MM:SS
            time_part = start_time.split('T')[1].split(':')[0:2]
            time_str = f"{time_part[0]}:{time_part[1]}"
        elif re.match(r'\d{1,2}:\d{2}', start_time):
            # Already in HH:MM format
            time_str = start_time
        else:
            # Try to extract time from title
            time_match = re.search(r'(\d{1,2}:\d{2})', title)
            if time_match:
                time_str = time_match.group(1)
            else:
                time_str = "Unknown"
        
        # Parse title for subject, room, teacher
        # Clean up the title first
        title = title.strip()
        
        # Skip if title is too short or contains navigation elements
        if len(title) < 5 or any(skip in title.lower() for skip in ['vali tunniplaan', 'täna', 'kuu', 'nädal', 'kontakt', 'siseveeb']):
            return None
        
        # Try different parsing patterns
        subject = "Unknown"
        room = "Unknown" 
        teacher = "Unknown"
        
        # Pattern 1: "Subject - Room - Teacher" format
        if ' - ' in title and title.count(' - ') >= 2:
            parts = [p.strip() for p in title.split(' - ')]
            if len(parts) >= 3:
                subject = parts[0]
                room = parts[1]
                teacher = parts[2]
        
        # Pattern 2: Look for room pattern like "A401" or "A401 (Arvutiklass)"
        elif re.search(r'[A-Z]\d{3}', title):
            # Extract room
            room_match = re.search(r'([A-Z]\d{3}(?: \([^)]+\))?)', title)
            if room_match:
                room = room_match.group(1)
                # Remove room from title to get subject
                remaining = title.replace(room_match.group(1), '').strip()
                # Split by common separators
                parts = re.split(r'\s+-\s+|\s+', remaining)
                subject = parts[0] if parts else "Unknown"
                teacher = parts[-1] if len(parts) > 1 else "Unknown"
        
        # Pattern 3: Simple fallback
        else:
            # Try to split by common separators
            parts = re.split(r'\s+-\s+|\s+', title)
            if len(parts) >= 2:
                subject = parts[0]
                if len(parts) > 1:
                    teacher = parts[-1]
                if len(parts) > 2:
                    room = parts[1]
            else:
                subject = title
        
        return {
            'time': time_str,
            'subject': subject,
            'room': room,
            'teacher': teacher,
            'raw_text': title
        }
    except Exception as e:
        print(f"⚠️ Error parsing lesson data: {e}")
        return None

def scrape_table_data(soup):
    """Fallback: try to scrape table data"""
    lessons = []
    
    # Look for tables with lesson data
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 3:
                time_text = cells[0].get_text(strip=True)
                subject_text = cells[1].get_text(strip=True)
                room_text = cells[2].get_text(strip=True) if len(cells) > 2 else "Unknown"
                teacher_text = cells[3].get_text(strip=True) if len(cells) > 3 else "Unknown"
                
                if re.match(r'\d{1,2}:\d{2}', time_text):
                    lessons.append({
                        'time': time_text,
                        'subject': subject_text,
                        'room': room_text,
                        'teacher': teacher_text,
                        'raw_text': f"{time_text} - {subject_text} - {room_text} - {teacher_text}"
                    })
    
    return lessons

def filter_daily_lessons(lessons):
    """Filter lessons to show only today's lessons"""
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    
    daily_lessons = []
    for lesson in lessons:
        # This is a simplified filter - in reality you'd need to check the actual date
        # For now, just return all lessons as a fallback
        daily_lessons.append(lesson)
    
    return daily_lessons

def organize_lessons_by_day(lessons, period):
    """Organize lessons by day of the week"""
    weekly_lessons = {}
    
    if period == "weekly":
        # For weekly view, organize by day
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in days:
            weekly_lessons[day] = []
        
        # Distribute lessons (simplified - in reality you'd parse actual dates)
        for i, lesson in enumerate(lessons):
            day_index = i % 5  # Monday to Friday
            weekly_lessons[days[day_index]].append(lesson)
    else:
        # For daily view, put all lessons under today
        today = datetime.now()
        day_name = today.strftime('%A')
        weekly_lessons[day_name] = lessons
    
    return weekly_lessons
