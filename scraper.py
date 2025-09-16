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

def handle_additional_auth(driver, username, password):
    """Handle additional authentication steps like 2FA"""
    try:
        # Check if there are additional auth fields
        auth_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='password'], input[type='number']")
        print(f"🔍 Found {len(auth_fields)} input fields for additional auth")
        
        # Look for 2FA code field
        for field in auth_fields:
            field_name = field.get_attribute('name') or field.get_attribute('id') or ''
            field_placeholder = field.get_attribute('placeholder') or ''
            print(f"  Field: {field_name} - {field_placeholder}")
            
            # Check if this looks like a 2FA field
            if any(keyword in (field_name + field_placeholder).lower() for keyword in ['code', 'token', '2fa', 'verification', 'otp']):
                print("🔍 2FA field detected - this requires manual intervention")
                return {
                    'success': False,
                    'error': '2FA authentication required. Please disable 2FA or use a different authentication method.'
                }
        
        return {'success': True, 'message': 'No additional auth required'}
        
    except Exception as e:
        print(f"⚠️ Error checking additional auth: {e}")
        return {'success': True, 'message': 'Could not check additional auth'}

def scrape_internal_timetable():
    """Scrape the internal timetable from siseveeb.voco.ee using Selenium"""
    try:
        # Get credentials from environment variables
        username = os.getenv("VOCO_USERNAME")
        password = os.getenv("VOCO_PASSWORD")
        two_factor_code = os.getenv("VOCO_2FA_CODE")
        
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
                # Wait for login form to be present
                wait_login = WebDriverWait(driver, 10)
                wait_login.until(EC.presence_of_element_located((By.NAME, "username")))
                
                # Find username and password fields
                username_field = driver.find_element(By.NAME, "username")
                password_field = driver.find_element(By.NAME, "password")
                
                # Clear fields and enter credentials
                username_field.clear()
                password_field.clear()
                username_field.send_keys(username)
                password_field.send_keys(password)
                
                # Check if there's a two-level password field (2FA)
                try:
                    two_level_field = driver.find_element(By.NAME, "two_level_password")
                    print("🔍 Two-level password field detected - this requires 2FA")
                    
                    if two_factor_code:
                        print("🔐 2FA code provided, entering it...")
                        two_level_field.clear()
                        two_level_field.send_keys(two_factor_code)
                    else:
                        return {
                            'success': False,
                            'error': 'Two-level authentication required. Please provide the 2FA code in the .env file as VOCO_2FA_CODE'
                        }
                except:
                    print("✅ No two-level password field found")
                
                # Find and click login button
                login_button = driver.find_element(By.ID, "form_submit")
                login_button.click()
                
                print("🔐 Login form submitted, waiting for authentication...")
                time.sleep(8)  # Wait for login to complete
                
                # Check if we're still on login page (authentication failed)
                if "login" in driver.current_url.lower() or "autoriseerimine" in driver.page_source.lower():
                    print("❌ Authentication failed - still on login page")
                    
                    # Check for error messages or additional auth requirements
                    error_elements = driver.find_elements(By.CSS_SELECTOR, ".alert, .error, .warning, .text-danger")
                    if error_elements:
                        error_text = error_elements[0].text.strip()
                        print(f"🔍 Error message found: {error_text}")
                        return {
                            'success': False,
                            'error': f'Authentication failed: {error_text}'
                        }
                    
                    # Check for additional authentication requirements
                    additional_auth = handle_additional_auth(driver, username, password)
                    if not additional_auth['success']:
                        return additional_auth
                    
                    return {
                        'success': False,
                        'error': 'Authentication failed. Please check credentials in .env file'
                    }
                else:
                    print("✅ Authentication successful")
                
            except Exception as e:
                print(f"❌ Login failed: {e}")
                return {
                    'success': False,
                    'error': f'Login failed: {str(e)}'
                }
            
            # Navigate to the reminders page which contains the daily plan
            timetable_url = 'https://siseveeb.voco.ee/info/meeldetuletused'
            print(f"📅 Accessing daily plan: {timetable_url}")
            
            driver.get(timetable_url)
            time.sleep(5)  # Wait for initial page load
            
            # Wait for the dynamic content blocks to load
            print("⏳ Waiting for dynamic content to load...")
            wait = WebDriverWait(driver, 15)
            
            # Wait for either the daily plan or weekly timetable blocks to load
            try:
                # Try to wait for daily plan content
                wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='home_page_block_3']//table | //div[@id='home_page_block_4']//table")))
                print("✅ Found timetable content")
            except:
                try:
                    # Fallback: wait for any table in the home page blocks
                    wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@id, 'home_page_block')]//table")))
                    print("✅ Found table in home page blocks")
                except:
                    print("⚠️ No timetable tables found, continuing...")
            
            # Additional wait for content to fully load
            time.sleep(3)
            
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
            
            # Look for timetable data in the home page blocks
            lessons = []
            
            # Method 1: Look for daily plan (home_page_block_3) or weekly timetable (home_page_block_4)
            daily_plan_block = soup.find('div', {'id': 'home_page_block_3'})
            weekly_plan_block = soup.find('div', {'id': 'home_page_block_4'})
            
            print(f"📊 Daily plan block found: {daily_plan_block is not None}")
            print(f"📊 Weekly plan block found: {weekly_plan_block is not None}")
            
            # Check daily plan first
            if daily_plan_block:
                print("🔍 Checking daily plan block...")
                tables = daily_plan_block.find_all('table')
                print(f"  Found {len(tables)} tables in daily plan")
                
                for i, table in enumerate(tables):
                    print(f"  Table {i+1}: {len(table.find_all('tr'))} rows")
                    
                    # Check if this table has lesson data
                    header_row = table.find('tr')
                    if header_row:
                        header_cells = header_row.find_all(['th', 'td'])
                        header_text = ' '.join([cell.get_text(strip=True) for cell in header_cells])
                        print(f"    Headers: {header_text}")
                        
                        # Check if this looks like a lesson table
                        if any(header in header_text for header in ['Aeg', 'Nimetus', 'Õpetaja', 'Ruum', 'Tund', 'Aine']):
                            print(f"    ✅ Found lesson table!")
                            
                            rows = table.find_all('tr')[1:]  # Skip header row
                            for j, row in enumerate(rows):
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 3:  # Should have at least time, subject, teacher
                                    time_text = cells[0].get_text(strip=True)
                                    subject_text = cells[1].get_text(strip=True)
                                    teacher_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                                    room_text = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                                    
                                    # Only add if it looks like a lesson (has time pattern or subject)
                                    if re.match(r'\d{1,2}:\d{2}', time_text) or subject_text.strip():
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
                                        print(f"      ⚠️ Skipped row: {time_text} | {subject_text}")
            
            # Check weekly plan if daily plan didn't have data
            if not lessons and weekly_plan_block:
                print("🔍 Checking weekly plan block...")
                tables = weekly_plan_block.find_all('table')
                print(f"  Found {len(tables)} tables in weekly plan")
                
                for i, table in enumerate(tables):
                    print(f"  Table {i+1}: {len(table.find_all('tr'))} rows")
                    
                    # Check if this table has lesson data
                    header_row = table.find('tr')
                    if header_row:
                        header_cells = header_row.find_all(['th', 'td'])
                        header_text = ' '.join([cell.get_text(strip=True) for cell in header_cells])
                        print(f"    Headers: {header_text}")
                        
                        # Check if this looks like a lesson table
                        if any(header in header_text for header in ['Aeg', 'Nimetus', 'Õpetaja', 'Ruum', 'Tund', 'Aine']):
                            print(f"    ✅ Found lesson table!")
                            
                            rows = table.find_all('tr')[1:]  # Skip header row
                            for j, row in enumerate(rows):
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 3:  # Should have at least time, subject, teacher
                                    time_text = cells[0].get_text(strip=True)
                                    subject_text = cells[1].get_text(strip=True)
                                    teacher_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                                    room_text = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                                    
                                    # Only add if it looks like a lesson (has time pattern or subject)
                                    if re.match(r'\d{1,2}:\d{2}', time_text) or subject_text.strip():
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
                                        print(f"      ⚠️ Skipped row: {time_text} | {subject_text}")
            
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