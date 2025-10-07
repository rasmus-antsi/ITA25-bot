"""
Simplified VOCO Scraper for Discord Bot
"""
import requests
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

class VOCOScraper:
    """Simplified VOCO scraper for ITA25 and ITS25 lessons"""
    
    # Program codes mapping
    PROGRAM_CODES = {
        'ITA25': 2078,  # ITA25
        'ITS25': 2028   # ITS25 (2028)
    }
    
    def __init__(self, program_code='ITA25'):
        self.base_url = "https://siseveeb.voco.ee/veebivormid/tunniplaan"
        self.program_code = program_code
        self.oppegrupp = self.PROGRAM_CODES.get(program_code, 2078)  # Default to ITA25
        self.session = requests.Session()
        self.session.timeout = 30
    
    def get_todays_lessons(self) -> List[Dict]:
        """Get today's lessons for the selected program"""
        today = datetime.now().strftime('%d.%m.%Y')
        
        try:
            # Fetch the schedule page
            url = f"{self.base_url}/tunniplaan"
            params = {
                "oppegrupp": self.oppegrupp,
                "nadal": today,
                "no_export": 1
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            events = self._parse_events(soup)
            
            # Filter for today's lessons and remove "Tegevuspäev"
            today_lessons = []
            seen_lessons = set()
            
            for event in events:
                event_date = event.get('date', '')
                # Convert today's date to ISO format for comparison
                today_iso = datetime.now().strftime('%Y-%m-%d')
                if event_date == today_iso:
                    subject = event.get('subject', '')
                    # Skip "Tegevuspäev" and empty subjects
                    if subject and subject != 'Tegevuspäev' and subject.strip():
                        # Group by time slot only (not subject name)
                        start_time = event.get('start_time', '')
                        end_time = event.get('end_time', '')
                        lesson_key = f"{start_time}_{end_time}"
                        if lesson_key not in seen_lessons:
                            today_lessons.append(event)
                            seen_lessons.add(lesson_key)
                        else:
                            # If same time slot, merge with existing lesson
                            for i, existing_lesson in enumerate(today_lessons):
                                if (existing_lesson.get('start_time') == start_time and
                                    existing_lesson.get('end_time') == end_time):
                                    # Add teacher and room to existing lesson
                                    if 'teachers' not in existing_lesson:
                                        existing_lesson['teachers'] = [existing_lesson.get('teacher', '')]
                                        existing_lesson['rooms'] = [existing_lesson.get('room', '')]
                                        existing_lesson['subjects'] = [existing_lesson.get('subject', '')]
                                    existing_lesson['teachers'].append(event.get('teacher', ''))
                                    existing_lesson['rooms'].append(event.get('room', ''))
                                    existing_lesson['subjects'].append(subject)
                                    break
            
            return today_lessons
            
        except Exception as e:
            print(f"Error fetching lessons: {e}")
            return []
    
    def get_lessons_for_date(self, date_str: str) -> List[Dict]:
        """Get lessons for a specific date for the selected program"""
        try:
            # Handle 'tomorrow' parameter
            if date_str == 'tomorrow':
                tomorrow = datetime.now() + timedelta(days=1)
                date_str = tomorrow.strftime('%d.%m.%Y')
            
            # Fetch the schedule page
            url = f"{self.base_url}/tunniplaan"
            params = {
                "oppegrupp": self.oppegrupp,
                "nadal": date_str,
                "no_export": 1
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            events = self._parse_events(soup)
            
            # Convert date_str to ISO format for comparison
            if date_str == 'tomorrow':
                target_date_iso = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                try:
                    target_date_iso = datetime.strptime(date_str, '%d.%m.%Y').strftime('%Y-%m-%d')
                except ValueError:
                    print(f"Invalid date format: {date_str}")
                    return []
            
            # Filter for target date's lessons and remove "Tegevuspäev"
            lessons = []
            seen_lessons = set()
            
            for event in events:
                event_date = event.get('date', '')
                if event_date == target_date_iso:
                    subject = event.get('subject', '')
                    # Skip "Tegevuspäev" and empty subjects
                    if subject and subject != 'Tegevuspäev' and subject.strip():
                        # Group by time slot only (not subject name)
                        start_time = event.get('start_time', '')
                        end_time = event.get('end_time', '')
                        lesson_key = f"{start_time}_{end_time}"
                        if lesson_key not in seen_lessons:
                            lessons.append(event)
                            seen_lessons.add(lesson_key)
                        else:
                            # If same time slot, merge with existing lesson
                            for i, existing_lesson in enumerate(lessons):
                                if (existing_lesson.get('start_time') == start_time and
                                    existing_lesson.get('end_time') == end_time):
                                    # Add teacher and room to existing lesson
                                    if 'teachers' not in existing_lesson:
                                        existing_lesson['teachers'] = [existing_lesson.get('teacher', '')]
                                        existing_lesson['rooms'] = [existing_lesson.get('room', '')]
                                        existing_lesson['subjects'] = [existing_lesson.get('subject', '')]
                                    existing_lesson['teachers'].append(event.get('teacher', ''))
                                    existing_lesson['rooms'].append(event.get('room', ''))
                                    existing_lesson['subjects'].append(subject)
                                    break
            
            return lessons
            
        except Exception as e:
            print(f"Error fetching lessons for {date_str}: {e}")
            return []
    
    def _parse_events(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse events from HTML content"""
        events = []
        
        # Find JavaScript containing events data
        script_tags = soup.find_all('script')
        
        for script in script_tags:
            if script.string and 'events:' in script.string:
                events_match = re.search(r'events:\s*\[(.*?)\]', script.string, re.DOTALL)
                if events_match:
                    events_text = events_match.group(1)
                    events = self._parse_events_from_js(events_text)
                    break
        
        return events
    
    def _parse_events_from_js(self, events_text: str) -> List[Dict]:
        """Parse individual events from JavaScript events array"""
        events = []
        
        # Find all event objects in the JavaScript
        event_pattern = r"\{[^}]*plan_id:'[^']*'[^}]*\}"
        event_matches = re.findall(event_pattern, events_text)
        
        for event_match in event_matches:
            try:
                event = self._extract_event_data(event_match)
                if event:
                    events.append(event)
            except Exception as e:
                print(f"Failed to parse event: {e}")
                continue
        
        return events
    
    def _extract_event_data(self, event_text: str) -> Optional[Dict]:
        """Extract structured data from a single event"""
        # Extract basic fields
        plan_id = re.search(r"plan_id:'([^']*)'", event_text)
        title = re.search(r"title:'([^']*)'", event_text)
        start = re.search(r"start:'([^']*)'", event_text)
        end = re.search(r"end:'([^']*)'", event_text)
        
        if not all([plan_id, title, start, end]):
            return None
        
        # Clean and process the data
        clean_title = self._clean_html(title.group(1))
        
        event = {
            'plan_id': plan_id.group(1),
            'title': clean_title,
            'start': start.group(1),
            'end': end.group(1),
            'start_time': self._extract_time(start.group(1)),
            'end_time': self._extract_time(end.group(1)),
            'date': self._extract_date(start.group(1)),
            'subject': self._extract_subject_name(clean_title),
            'teacher': self._extract_teacher_name(clean_title),
            'room': self._extract_room_info(clean_title)
        }
        
        return event
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        return re.sub(r'<[^>]+>', '', text)
    
    def _extract_teacher_name(self, title: str) -> str:
        """Extract teacher name from lesson title"""
        parts = title.split(';')
        if len(parts) >= 2:
            return parts[1].strip()
        return 'Tundmatu'
    
    def _extract_room_info(self, title: str) -> str:
        """Extract room information from lesson title"""
        # Try different room patterns
        room_patterns = [
            r'[A-Z]\d+[A-Z]?\s*\([^)]+\)',  # A310 (Arvutiklass)
            r'[A-Z]\d+[A-Z]?',  # A310
            r'\([^)]+\)',  # (Arvutiklass)
        ]
        
        for pattern in room_patterns:
            room_match = re.search(pattern, title)
            if room_match:
                return room_match.group(0)
        
        return 'Tundmatu ruum'
    
    def _extract_subject_name(self, title: str) -> str:
        """Extract subject name from lesson title"""
        parts = title.split(';')
        return parts[0].strip()
    
    def _extract_time(self, datetime_str: str) -> str:
        """Extract time from datetime string"""
        try:
            dt = datetime.fromisoformat(datetime_str.replace('+03:00', ''))
            return dt.strftime('%H:%M')
        except:
            return datetime_str
    
    def _extract_date(self, datetime_str: str) -> str:
        """Extract date from datetime string"""
        try:
            dt = datetime.fromisoformat(datetime_str.replace('+03:00', ''))
            return dt.strftime('%Y-%m-%d')
        except:
            return datetime_str.split('T')[0]
