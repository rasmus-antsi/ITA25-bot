#!/usr/bin/env python3
"""
Website Explorer for voco.ee timetable
This script explores the website structure to find where lesson data is stored
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def explore_with_requests():
    """Explore the website using requests to see the initial HTML"""
    print("🔍 Exploring with requests...")
    
    url = "https://voco.ee/tunniplaan/?course=2078"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Page title: {soup.title.string if soup.title else 'No title'}")
        
        # Look for any scripts that might contain data
        scripts = soup.find_all('script')
        print(f"📜 Found {len(scripts)} script tags")
        
        for i, script in enumerate(scripts):
            if script.string:
                content = script.string
                # Look for potential data patterns
                if any(keyword in content.lower() for keyword in ['event', 'lesson', 'timetable', 'calendar', 'fc-']):
                    print(f"\n🎯 Script {i+1} contains relevant keywords:")
                    print(f"Length: {len(content)} characters")
                    print(f"First 200 chars: {content[:200]}...")
                    
                    # Look for JSON data
                    json_patterns = [
                        r'var\s+\w+\s*=\s*(\{.*?\});',
                        r'window\.\w+\s*=\s*(\{.*?\});',
                        r'data:\s*(\{.*?\})',
                        r'events:\s*(\[.*?\])',
                    ]
                    
                    for pattern in json_patterns:
                        matches = re.findall(pattern, content, re.DOTALL)
                        if matches:
                            print(f"Found JSON pattern: {pattern}")
                            for match in matches[:2]:  # Show first 2 matches
                                try:
                                    json_data = json.loads(match)
                                    print(f"Valid JSON found: {json.dumps(json_data, indent=2)[:500]}...")
                                except:
                                    print(f"Invalid JSON: {match[:100]}...")
        
        # Look for any elements that might contain calendar data
        calendar_elements = soup.find_all(['div', 'table', 'ul'], class_=re.compile(r'fc-|calendar|timetable|event'))
        print(f"\n📅 Found {len(calendar_elements)} potential calendar elements")
        
        for elem in calendar_elements[:3]:  # Show first 3
            print(f"Element: {elem.name} class='{elem.get('class')}'")
            print(f"Content: {elem.get_text()[:100]}...")
        
        return soup
        
    except Exception as e:
        print(f"❌ Error with requests: {e}")
        return None

def explore_with_selenium():
    """Explore the website using Selenium to see the dynamic content"""
    print("\n🔍 Exploring with Selenium...")
    
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
            url = "https://voco.ee/tunniplaan/?course=2078"
            print(f"🌐 Navigating to: {url}")
            driver.get(url)
            
            # Wait for page to load
            wait = WebDriverWait(driver, 20)
            
            print("⏳ Waiting for page to load...")
            time.sleep(5)
            
            # Check if course selector exists
            try:
                course_select = wait.until(EC.presence_of_element_located((By.ID, "course_select")))
                print("✅ Found course selector")
                
                # Get all course options
                options = course_select.find_elements(By.TAG_NAME, "option")
                print(f"📋 Found {len(options)} course options:")
                for option in options:
                    print(f"  - {option.get_attribute('value')}: {option.text}")
                
                # Select course 2078 if available
                try:
                    course_2078 = driver.find_element(By.CSS_SELECTOR, "option[value='2078']")
                    course_2078.click()
                    print("✅ Selected course 2078")
                    time.sleep(3)
                except:
                    print("⚠️ Course 2078 not found, continuing with current selection")
                
            except Exception as e:
                print(f"⚠️ Course selector not found: {e}")
            
            # Look for calendar elements
            print("\n📅 Looking for calendar elements...")
            
            # Try different selectors for calendar
            calendar_selectors = [
                ".fc",
                ".fullcalendar",
                "[class*='calendar']",
                "[class*='fc-']",
                ".timetable",
                ".schedule"
            ]
            
            for selector in calendar_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ Found {len(elements)} elements with selector: {selector}")
                    for elem in elements[:2]:  # Show first 2
                        print(f"  Element: {elem.tag_name} class='{elem.get_attribute('class')}'")
                        print(f"  Text: {elem.text[:100]}...")
                else:
                    print(f"❌ No elements found with selector: {selector}")
            
            # Look for any events or lessons
            print("\n🎯 Looking for events/lessons...")
            
            event_selectors = [
                ".fc-event",
                ".event",
                ".lesson",
                "[class*='event']",
                "[class*='lesson']",
                ".fc-event-container .fc-event",
                ".fc-content .fc-event"
            ]
            
            for selector in event_selectors:
                events = driver.find_elements(By.CSS_SELECTOR, selector)
                if events:
                    print(f"✅ Found {len(events)} events with selector: {selector}")
                    for i, event in enumerate(events[:3]):  # Show first 3
                        print(f"  Event {i+1}: {event.text[:100]}...")
                        print(f"    Classes: {event.get_attribute('class')}")
                        print(f"    Data attributes: {[attr for attr in event.get_property('attributes') if attr['name'].startswith('data-')]}")
                else:
                    print(f"❌ No events found with selector: {selector}")
            
            # Get page source and look for data
            print("\n📄 Analyzing page source...")
            page_source = driver.page_source
            
            # Look for JSON data in the page
            json_patterns = [
                r'var\s+\w+\s*=\s*(\{.*?\});',
                r'window\.\w+\s*=\s*(\{.*?\});',
                r'data:\s*(\{.*?\})',
                r'events:\s*(\[.*?\])',
                r'"events":\s*(\[.*?\])',
                r'"data":\s*(\[.*?\])',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, page_source, re.DOTALL)
                if matches:
                    print(f"🎯 Found JSON pattern: {pattern}")
                    for i, match in enumerate(matches[:2]):  # Show first 2
                        try:
                            json_data = json.loads(match)
                            print(f"  Valid JSON {i+1}: {json.dumps(json_data, indent=2)[:500]}...")
                        except:
                            print(f"  Invalid JSON {i+1}: {match[:100]}...")
            
            # Look for specific data attributes
            print("\n🔍 Looking for data attributes...")
            elements_with_data = driver.find_elements(By.CSS_SELECTOR, "[data-start], [data-date], [data-event]")
            print(f"Found {len(elements_with_data)} elements with data attributes")
            
            for elem in elements_with_data[:5]:  # Show first 5
                attrs = {}
                for attr in ['data-start', 'data-date', 'data-event', 'data-title', 'data-time']:
                    value = elem.get_attribute(attr)
                    if value:
                        attrs[attr] = value
                if attrs:
                    print(f"  Element: {elem.tag_name} {attrs}")
            
            # Check for AJAX requests or API endpoints
            print("\n🌐 Looking for network requests...")
            logs = driver.get_log('performance')
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    url = message['message']['params']['response']['url']
                    if any(keyword in url.lower() for keyword in ['api', 'data', 'events', 'timetable', 'course']):
                        print(f"  API/Data URL: {url}")
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"❌ Error with Selenium: {e}")

def main():
    print("🚀 Starting website exploration...")
    print("=" * 50)
    
    # First try with requests
    soup = explore_with_requests()
    
    # Then try with Selenium
    explore_with_selenium()
    
    print("\n" + "=" * 50)
    print("✅ Exploration complete!")

if __name__ == "__main__":
    main()
