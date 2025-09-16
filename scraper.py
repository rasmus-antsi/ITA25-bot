#!/usr/bin/env python3
"""
Advanced scraper for voco.ee timetable
Based on exploration findings - uses Selenium to get the actual lesson data
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import time
import re

def scrape_timetable():
    """Scrape the actual timetable from voco.ee using Selenium"""
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Navigate to the timetable page
            url = "https://voco.ee/tunniplaan/?course=2078"
            print(f"🌐 Navigating to: {url}")
            driver.get(url)
            
            # Wait for page to load
            wait = WebDriverWait(driver, 20)
            print("⏳ Waiting for page to load...")
            time.sleep(5)
            
            # Wait for the calendar to appear
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "fc")))
            print("✅ Calendar loaded")
            
            # Get all events from the calendar
            events = driver.find_elements(By.CSS_SELECTOR, ".fc-event")
            print(f"📅 Found {len(events)} events")
            
            if not events:
                print("❌ No events found")
                return {'success': False, 'error': 'No events found in calendar'}
            
            # Parse events into lessons
            lessons = []
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for event in events:
                try:
                    # Get event text
                    event_text = event.text
                    print(f"📝 Event: {event_text[:100]}...")
                    
                    # Extract time from the event text
                    time_match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', event_text)
                    if time_match:
                        start_time, end_time = time_match.groups()
                        time_str = f"{start_time} - {end_time}"
                    else:
                        time_str = "Unknown time"
                    
                    # Extract subject, room, and teacher
                    lines = event_text.split('\n')
                    if len(lines) >= 2:
                        subject_line = lines[1] if len(lines) > 1 else lines[0]
                        
                        # Extract room
                        room = ""
                        room_patterns = [
                            r'Kopli A - (A\d+)',  # Kopli A - A401
                            r'\(A\d+\)',          # (A401)
                            r'A\d+',              # A401
                        ]
                        
                        for pattern in room_patterns:
                            room_match = re.search(pattern, subject_line)
                            if room_match:
                                room = room_match.group(1) if room_match.groups() else room_match.group(0)
                                break
                        
                        # Extract teacher
                        teacher = ""
                        teacher_patterns = [
                            r'([A-Z][a-z]+ [A-Z][a-z]+)',  # First Last
                            r'([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+)',  # First Middle Last
                        ]
                        
                        for pattern in teacher_patterns:
                            teacher_match = re.search(pattern, subject_line)
                            if teacher_match:
                                teacher = teacher_match.group(1)
                                break
                        
                        # Clean up subject
                        subject = subject_line
                        subject = re.sub(r'Kopli A.*', '', subject).strip()
                        subject = re.sub(r'\([^)]*\)', '', subject).strip()
                        subject = re.sub(r'[A-Z][a-z]+ [A-Z][a-z]+.*', '', subject).strip()
                        subject = re.sub(r'\s+', ' ', subject).strip()
                        
                        lesson = {
                            'time': time_str,
                            'subject': subject,
                            'room': room,
                            'teacher': teacher,
                            'raw_text': event_text
                        }
                        
                        lessons.append(lesson)
                        print(f"  ✅ Parsed: {time_str} - {subject} - {room} - {teacher}")
                    
                except Exception as e:
                    print(f"❌ Error parsing event: {e}")
                    continue
            
            # Group lessons by day (for now, we'll distribute them across the week)
            weekly_lessons = {}
            for i, lesson in enumerate(lessons):
                day_name = day_names[i % 7]
                if day_name not in weekly_lessons:
                    weekly_lessons[day_name] = []
                weekly_lessons[day_name].append(lesson)
            
            # Get week range
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            week_range = f"{week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m.%Y')}"
            
            return {
                'success': True,
                'lessons': weekly_lessons,
                'week_range': week_range,
                'source': 'Live data from voco.ee',
                'total_events': len(lessons)
            }
            
        finally:
            driver.quit()
            
    except Exception as e:
        return {'success': False, 'error': f'Scraping error: {str(e)}'}

def main():
    """Test the scraper"""
    print("🚀 Testing timetable scraper...")
    print("=" * 50)
    
    result = scrape_timetable()
    
    if result['success']:
        print(f"✅ Success! Found {result['total_events']} events")
        print(f"📅 Week: {result['week_range']}")
        print(f"📊 Days with lessons: {len(result['lessons'])}")
        
        for day, day_lessons in result['lessons'].items():
            if day_lessons:
                print(f"\n📅 {day}:")
                for lesson in day_lessons:
                    print(f"  🕐 {lesson['time']} - {lesson['subject']} - {lesson['room']} - {lesson['teacher']}")
    else:
        print(f"❌ Error: {result['error']}")

if __name__ == "__main__":
    main()
