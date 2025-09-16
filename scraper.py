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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

# Load environment variables
load_dotenv()

def scrape_internal_timetable():
    """Scrape the internal timetable from siseveeb.voco.ee using Selenium"""
    try:
        # Get credentials from environment variables
        username = os.getenv("VOCO_USERNAME")
        password = os.getenv("VOCO_PASSWORD")
        
        if not username or not password:
            return {
                'success': False, 
                'error': 'Missing credentials. Please set VOCO_USERNAME and VOCO_PASSWORD in .env file'
            }
        
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
            print("🔐 Authenticating with siseveeb.voco.ee...")
            
            # First, go to the login page
            login_url = 'https://siseveeb.voco.ee/'
            driver.get(login_url)
            time.sleep(3)
            
            # Look for login form elements
            try:
                # Try to find username and password fields
                username_field = driver.find_element(By.NAME, "username")
                password_field = driver.find_element(By.NAME, "password")
                
                username_field.send_keys(username)
                password_field.send_keys(password)
                
                # Look for login button
                login_button = driver.find_element(By.XPATH, "//input[@type='submit'] | //button[contains(text(), 'Login')] | //button[contains(text(), 'Sisene')]")
                login_button.click()
                
                time.sleep(5)  # Wait for login to complete
                
            except Exception as e:
                print(f"⚠️ Could not find login form: {e}")
                # Try alternative login method
                try:
                    # Try to find and click login link
                    login_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Login')] | //a[contains(text(), 'Sisene')]")
                    login_link.click()
                    time.sleep(3)
                    
                    username_field = driver.find_element(By.NAME, "username")
                    password_field = driver.find_element(By.NAME, "password")
                    
                    username_field.send_keys(username)
                    password_field.send_keys(password)
                    
                    login_button = driver.find_element(By.XPATH, "//input[@type='submit'] | //button[contains(text(), 'Login')] | //button[contains(text(), 'Sisene')]")
                    login_button.click()
                    
                    time.sleep(5)
                    
                except Exception as e2:
                    print(f"⚠️ Alternative login also failed: {e2}")
            
            print("✅ Authentication attempted")
            
            # Navigate to the reminders page which contains the daily plan
            timetable_url = 'https://siseveeb.voco.ee/info/meeldetuletused'
            print(f"📅 Accessing daily plan: {timetable_url}")
            
            driver.get(timetable_url)
            time.sleep(10)  # Wait for JavaScript to load
            
            # Wait for the page to load
            wait = WebDriverWait(driver, 20)
            
            # Try to wait for the daily plan table
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "//table[contains(., 'Aeg') or contains(., 'Nimetus') or contains(., 'Õpetaja')]")))
                print("✅ Found daily plan table")
            except:
                try:
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                    print("✅ Found table element")
                except:
                    print("⚠️ No table elements found, continuing...")
            
            # Get the page source after JavaScript execution
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Look for timetable data
            print("🔍 Parsing timetable data...")
            print(f"📄 Page title: {soup.title.string if soup.title else 'No title'}")
            
            # Debug: Save page content for analysis
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            print("💾 Saved page content to debug_page.html for analysis")
            
            # Look for various possible timetable structures
            lessons = []
            
            # Method 1: Look for the daily plan table specifically
            all_tables = soup.find_all('table')
            print(f"📊 Found {len(all_tables)} tables")
            
            for i, table in enumerate(all_tables):
                print(f"  Table {i+1}: {len(table.find_all('tr'))} rows")
                
                # Check if this table has the daily plan headers
                header_row = table.find('tr')
                if header_row:
                    header_cells = header_row.find_all(['th', 'td'])
                    header_text = ' '.join([cell.get_text(strip=True) for cell in header_cells])
                    print(f"    Headers: {header_text}")
                    
                    # Check if this looks like the daily plan table
                    if any(header in header_text for header in ['Aeg', 'Nimetus', 'Õpetaja', 'Ruum']):
                        print(f"    ✅ Found daily plan table!")
                        
                        rows = table.find_all('tr')[1:]  # Skip header row
                        for j, row in enumerate(rows):
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 4:  # Should have time, subject, teacher, room
                                time_text = cells[0].get_text(strip=True)
                                subject_text = cells[1].get_text(strip=True)
                                teacher_text = cells[2].get_text(strip=True)
                                room_text = cells[3].get_text(strip=True)
                                
                                # Only add if it looks like a lesson (has time pattern)
                                if re.match(r'\d{1,2}:\d{2}', time_text):
                                    lesson = {
                                        'time': time_text,
                                        'subject': subject_text,
                                        'room': room_text,
                                        'teacher': teacher_text,
                                        'raw_text': f"{time_text} - {subject_text} - {teacher_text} - {room_text}"
                                    }
                                    lessons.append(lesson)
                                    print(f"      ✅ Lesson: {lesson['raw_text']}")
                                else:
                                    print(f"      ⚠️ Skipped row (no time): {time_text}")
                        break  # Found the daily plan table, no need to check others
            
            # Method 2: Look for div elements with lesson data
            lesson_divs = soup.find_all('div', class_=re.compile(r'lesson|tund|event|fc-|calendar'))
            print(f"📅 Found {len(lesson_divs)} lesson divs")
            
            for div in lesson_divs:
                text_content = div.get_text(strip=True)
                if text_content and len(text_content) > 5:
                    print(f"  Div content: {text_content[:100]}...")
                    if any(keyword in text_content.lower() for keyword in [
                        'tund', 'lesson', 'õpetaja', 'teacher', 'ruum', 'room'
                    ]):
                        lessons.append({
                            'raw_text': text_content,
                            'time': 'Unknown',
                            'subject': 'Unknown',
                            'room': 'Unknown',
                            'teacher': 'Unknown'
                        })
            
            # Method 3: Look for any text that might contain lesson information
            page_text = soup.get_text()
            print(f"📝 Page text length: {len(page_text)} characters")
            
            # Look for time patterns (HH:MM - HH:MM)
            time_pattern = r'(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})'
            time_matches = re.findall(time_pattern, page_text)
            print(f"🕐 Found {len(time_matches)} time patterns: {time_matches[:5]}")
            
            # Look for Estonian subject patterns
            subject_patterns = [
                r'(Matemaatika|Eesti keel|Inglise keel|Füüsika|Keemia|Info|IT|Programmeerimine)',
                r'(õpetaja|teacher|ruum|room|tund|lesson)',
            ]
            
            for pattern in subject_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    print(f"📚 Found subjects: {matches[:5]}")
            
            if not lessons:
                # Return detailed debug information
                return {
                    'success': False,
                    'error': 'No timetable data found. Check debug_page.html for page structure.',
                    'page_title': soup.title.string if soup.title else 'No title',
                    'debug_info': {
                        'tables_found': len(all_tables),
                        'lesson_divs_found': len(lesson_divs),
                        'time_patterns_found': len(time_matches),
                        'page_text_length': len(page_text),
                        'content_preview': page_text[:1000] + '...' if page_text else 'No content'
                    }
                }
            
            print(f"✅ Found {len(lessons)} potential lessons")
            
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
            
        finally:
            driver.quit()
        
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
        if 'debug_info' in result:
            print(f"📊 Debug info: {result['debug_info']}")

if __name__ == "__main__":
    main()