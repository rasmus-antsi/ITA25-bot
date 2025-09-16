#!/usr/bin/env python3
"""
Scraper for voco.ee internal student portal timetable
Requires authentication to access the internal system
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def scrape_internal_timetable():
    """Scrape the internal timetable from siseveeb.voco.ee"""
    try:
        # Get credentials from environment variables
        username = os.getenv("VOCO_USERNAME")
        password = os.getenv("VOCO_PASSWORD")
        
        if not username or not password:
            return {
                'success': False, 
                'error': 'Missing credentials. Please set VOCO_USERNAME and VOCO_PASSWORD in .env file'
            }
        
        # Set up the authentication session
        session = requests.Session()
        
        # Set headers to mimic a real browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        print("🔐 Authenticating with siseveeb.voco.ee...")
        
        # Login to the internal system
        login_url = 'https://siseveeb.voco.ee/ajax_send'
        payload = {
            'form': 'login',
            'username': username,
            'password': password
        }
        
        login_response = session.post(login_url, data=payload)
        
        if login_response.status_code != 200:
            return {
                'success': False,
                'error': f'Login failed with status code: {login_response.status_code}'
            }
        
        print("✅ Authentication successful")
        
        # Navigate to the timetable page
        timetable_url = 'https://opilane.siseveeb.voco.ee/tunniplaan'
        print(f"📅 Accessing timetable: {timetable_url}")
        
        response = session.get(timetable_url)
        
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Failed to access timetable with status code: {response.status_code}'
            }
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for timetable data
        print("🔍 Parsing timetable data...")
        
        # Try to find timetable elements
        timetable_elements = soup.find_all(['table', 'div'], class_=re.compile(r'timetable|schedule|lesson|event'))
        
        if not timetable_elements:
            # Look for any structured data that might contain lessons
            all_tables = soup.find_all('table')
            all_divs = soup.find_all('div', class_=re.compile(r'fc-|calendar|event'))
            
            print(f"📊 Found {len(all_tables)} tables and {len(all_divs)} calendar divs")
            
            # Try to extract data from tables
            lessons = []
            for table in all_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:  # At least time, subject, room
                        row_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                        if any(keyword in row_text.lower() for keyword in ['tund', 'lesson', 'õpetaja', 'teacher', 'ruum', 'room']):
                            lessons.append({
                                'raw_text': row_text,
                                'time': cells[0].get_text(strip=True) if len(cells) > 0 else '',
                                'subject': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                                'room': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                                'teacher': cells[3].get_text(strip=True) if len(cells) > 3 else ''
                            })
            
            if lessons:
                print(f"✅ Found {len(lessons)} potential lessons in tables")
            else:
                # If no structured data found, return the page content for analysis
                return {
                    'success': False,
                    'error': 'No timetable data found. Page might require different parsing approach.',
                    'page_title': soup.title.string if soup.title else 'No title',
                    'content_preview': soup.get_text()[:500] + '...' if soup.get_text() else 'No content'
                }
        else:
            print(f"✅ Found {len(timetable_elements)} timetable elements")
            lessons = []
            
            for element in timetable_elements:
                # Extract lesson data from timetable elements
                text_content = element.get_text(strip=True)
                if text_content and len(text_content) > 10:  # Filter out empty elements
                    lessons.append({
                        'raw_text': text_content,
                        'time': 'Unknown',
                        'subject': 'Unknown',
                        'room': 'Unknown',
                        'teacher': 'Unknown'
                    })
        
        # Organize lessons by day (simplified approach)
        weekly_lessons = {}
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
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
            'source': 'Internal siseveeb.voco.ee',
            'total_lessons': len(lessons)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Scraping error: {str(e)}'
        }

def main():
    """Test the internal scraper"""
    print("🚀 Testing internal timetable scraper...")
    print("=" * 50)
    
    result = scrape_internal_timetable()
    
    if result['success']:
        print(f"✅ Success! Found {result['total_lessons']} lessons")
        print(f"📅 Week: {result['week_range']}")
        print(f"📊 Days with lessons: {len(result['lessons'])}")
        
        for day, day_lessons in result['lessons'].items():
            if day_lessons:
                print(f"\n📅 {day}:")
                for lesson in day_lessons:
                    print(f"  📝 {lesson['raw_text'][:100]}...")
    else:
        print(f"❌ Error: {result['error']}")
        if 'content_preview' in result:
            print(f"📄 Content preview: {result['content_preview']}")

if __name__ == "__main__":
    main()
