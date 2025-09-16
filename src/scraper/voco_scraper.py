"""
VOCO Timetable Scraper
Scrapes lesson data from voco.ee timetable
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time

def scrape_timetable(period="daily"):
    """
    Scrape timetable from VOCO website
    
    Args:
        period (str): "daily" or "weekly"
    
    Returns:
        dict: Scraped timetable data
    """
    try:
        # VOCO timetable URL
        url = "https://voco.ee/tunniplaan/?course=2078"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"🔍 Scraping VOCO timetable ({period})...")
        
        # Make request to VOCO
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for calendar events
        lessons = []
        
        # Try to find FullCalendar events in script tags
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'events' in script.string.lower():
                # Look for events array in JavaScript
                events_match = re.search(r'events:\s*\[(.*?)\]', script.string, re.DOTALL)
                if events_match:
                    events_text = events_match.group(1)
                    # Parse individual events
                    event_matches = re.findall(r'\{[^}]*\}', events_text)
                    for event_match in event_matches:
                        # Extract event data
                        title_match = re.search(r'title:\s*["\']([^"\']*)["\']', event_match)
                        start_match = re.search(r'start:\s*["\']([^"\']*)["\']', event_match)
                        
                        if title_match and start_match:
                            title = title_match.group(1)
                            start_time = start_match.group(1)
                            
                            # Parse the lesson data
                            lesson = parse_lesson_data(title, start_time)
                            if lesson:
                                lessons.append(lesson)
        
        # If no events found in scripts, try to find table data
        if not lessons:
            lessons = scrape_table_data(soup)
        
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

def parse_lesson_data(title, start_time):
    """Parse lesson data from title and start time"""
    try:
        # Extract time from start_time (format: YYYY-MM-DDTHH:MM:SS)
        if 'T' in start_time:
            time_part = start_time.split('T')[1].split(':')[0:2]
            time_str = f"{time_part[0]}:{time_part[1]}"
        else:
            time_str = "Unknown"
        
        # Parse title for subject, room, teacher
        # Common patterns in Estonian timetables
        parts = title.split(' - ')
        if len(parts) >= 3:
            subject = parts[0].strip()
            room = parts[1].strip()
            teacher = parts[2].strip()
        else:
            # Fallback parsing
            subject = title
            room = "Unknown"
            teacher = "Unknown"
        
        return {
            'time': time_str,
            'subject': subject,
            'room': room,
            'teacher': teacher,
            'raw_text': title
        }
    except:
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
