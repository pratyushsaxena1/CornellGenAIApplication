from flask import Flask, render_template, request, session, redirect, url_for
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import datetime
import sys
import ast
import os
import sqlite3
import json


sys.path.append(os.path.join(os.path.dirname(__file__), 'static', 'py'))
from testLLM import write_llm_prompt, get_llm_response


app = Flask(__name__)
app.secret_key = 'mol_and_prat_goat'  
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly','https://www.googleapis.com/auth/calendar.events']

def init_db():
    conn = sqlite3.connect('calendar_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            calendar_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            summary TEXT,
            start_time TEXT,
            end_time TEXT,
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')
    
    # Check if calendar_id column exists, if not add it (for existing databases)
    cursor.execute("PRAGMA table_info(events)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'calendar_id' not in columns:
        print("DEBUG: Adding calendar_id column to existing events table")
        cursor.execute('ALTER TABLE events ADD COLUMN calendar_id TEXT DEFAULT "primary"')
        # Update existing records to have calendar_id as 'primary'
        cursor.execute('UPDATE events SET calendar_id = "primary" WHERE calendar_id IS NULL')
    
    conn.commit()
    conn.close()

init_db()

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form')
def form():
    if 'credentials' not in session:
        return redirect(url_for('index'))
    return render_template('eventDetailsForm.html')

@app.route('/runLLM', methods=["GET", "POST"])
def runLLM():
    if 'credentials' not in session:
        return redirect(url_for('index'))

    if request.method == "POST":
        event_title = request.form.get("event_title")
        other_person_email = request.form.get("other_person_email")
        time_period = request.form.get("time_period")
        duration = request.form.get("duration")
        location = request.form.get("location")
        other_info = request.form.get("other_info")
        
        try:
            current_user_email = session.get('current_user_email')
            if not current_user_email:
                return "Error: User email not found in session. Please reconnect your Google Account."

            new_filename = write_llm_prompt(event_title, other_person_email, time_period, duration, location, other_info, current_user_email)
            llm_response = get_llm_response(new_filename)
            
            if llm_response == "UNAVAILABLE":
                return "No time available!"

            llm_response_dict = ast.literal_eval(llm_response)
            meeting_time_str = llm_response_dict['meeting time']
            duration_mins = int(float(llm_response_dict['duration']))

            start_dt = datetime.datetime.fromisoformat(meeting_time_str)
            end_dt = start_dt + datetime.timedelta(minutes=duration_mins)

            creds = Credentials(**session['credentials'])
            
            event_result = create_event(
                creds=creds, 
                summary=event_title,
                start_datetime=start_dt.isoformat(),
                end_datetime=end_dt.isoformat(),
                location=location,
                attendees=[other_person_email],
                description=other_info
            )
            
            time_unparsed = start_dt.strftime('%-I:%M %p') # e.g., 9:30 AM
            month, date, year = start_dt.month, start_dt.day, start_dt.year

            return f"Success! Your meeting time is on {month}/{date}/{year} at {time_unparsed}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    return "Please submit the form to run the LLM"

@app.route('/connect_google')
def connect_google():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    # --- FIX: Store credentials and email in the session ---
    session['credentials'] = credentials_to_dict(creds)
    
    service = build('calendar', 'v3', credentials=creds)
    
    # Get all calendars the user has access to
    calendar_list = service.calendarList().list().execute()
    calendars = calendar_list.get('items', [])
    
    # Get user email from primary calendar
    primary_calendar = service.calendarList().get(calendarId='primary').execute()
    user_email = primary_calendar['id']
    session['current_user_email'] = user_email
    
    now = datetime.datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + datetime.timedelta(days=7)).isoformat() + 'Z'
    
    # Fetch events from all calendars
    all_events = []
    for calendar in calendars:
        calendar_id = calendar['id']
        calendar_summary = calendar.get('summary', 'Unknown Calendar')
        print(f"DEBUG: Fetching events from calendar: {calendar_summary} ({calendar_id})")
        
        try:
            events_result = service.events().list(
                calendarId=calendar_id, 
                timeMin=time_min, 
                timeMax=time_max,
                singleEvents=True, 
                orderBy='startTime', 
                maxResults=50
            ).execute()
            calendar_events = events_result.get('items', [])
            
            # Add calendar_id to each event and filter out all-day events
            filtered_events = []
            for event in calendar_events:
                # Check if event is all-day (has 'date' instead of 'dateTime')
                start_time = event['start']
                end_time = event['end']
                
                # Skip all-day events (events with 'date' field instead of 'dateTime')
                if 'date' in start_time and 'dateTime' not in start_time:
                    print(f"DEBUG: Skipping all-day event: {event.get('summary', 'No Title')}")
                    continue
                
                event['calendar_id'] = calendar_id
                event['calendar_summary'] = calendar_summary
                filtered_events.append(event)
            
            all_events.extend(filtered_events)
            print(f"DEBUG: Found {len(filtered_events)} timed events in {calendar_summary} (excluded all-day events)")
        except Exception as e:
            print(f"DEBUG: Error fetching events from {calendar_summary}: {e}")
    
    print(f"DEBUG: Total events found across all calendars: {len(all_events)} for user {user_email}")
    
    conn = sqlite3.connect('calendar_data.db')
    cursor = conn.cursor()
    
    cursor.execute('INSERT OR REPLACE INTO users (email, last_updated) VALUES (?, CURRENT_TIMESTAMP)', (user_email,))
    print(f"DEBUG: Inserted/updated user {user_email}")
    
    cursor.execute('DELETE FROM events WHERE user_email = ?', (user_email,))
    print(f"DEBUG: Cleared existing events for {user_email}")
    
    events_inserted = 0
    for event in all_events:
        try:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = event.get('summary', 'No Title')
            event_id = event.get('id', '')
            calendar_id = event.get('calendar_id', 'primary')
            
            cursor.execute('INSERT INTO events (user_email, calendar_id, event_id, summary, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?)',
                           (user_email, calendar_id, event_id, summary, start, end))
            events_inserted += 1
            print(f"DEBUG: Inserted event: {summary} from {start} to {end} in calendar {event.get('calendar_summary', calendar_id)}")
        except Exception as e:
            print(f"DEBUG: Error inserting event {event.get('summary', 'Unknown')}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"DEBUG: Successfully inserted {events_inserted} events for {user_email}")
    
    return redirect(url_for('form'))

def create_event(creds, summary, start_datetime, end_datetime, location=None, attendees=None, description=None, calendar_id='primary'):
    service = build('calendar', 'v3', credentials=creds)
    
    event = {
        'summary': summary,
        'location': location if location else '',
        'description': description if description else '',
        'start': {'dateTime': start_datetime, 'timeZone': 'America/New_York'},
        'end': {'dateTime': end_datetime, 'timeZone': 'America/New_York'},
        'attendees': [{'email': email} for email in (attendees or [])],
    }

    event_result = service.events().insert(
        calendarId=calendar_id, 
        body=event,
        sendUpdates='all' 
    ).execute()
    return event_result

if __name__ == '__main__':
    app.run(debug=True)

