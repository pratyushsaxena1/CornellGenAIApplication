from flask import Flask, render_template, request, session
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
import sys
import ast
import os
import sqlite3
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'static', 'py'))
from testLLM import write_llm_prompt, get_llm_response


app = Flask(__name__)
app.secret_key = 'mol_and_prat_goat'  # Change this to a random secret key
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly','https://www.googleapis.com/auth/calendar.events']

# Database initialization
def init_db():
    conn = sqlite3.connect('calendar_data.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create events table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            event_id TEXT NOT NULL,
            summary TEXT,
            start_time TEXT,
            end_time TEXT,
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form')
def form():
    return render_template('eventDetailsForm.html')

@app.route('/runLLM', methods=["GET", "POST"])
def runLLM():
    if request.method == "POST":
        event_title = request.form.get("event_title")
        other_person_email = request.form.get("other_person_email")
        time_period = request.form.get("time_period")
        duration = request.form.get("duration")
        location = request.form.get("location")
        other_info = request.form.get("other_info")
        
        try:
            # Get current user's email from session
            current_user_email = session.get('current_user_email')
            
            new_filename = write_llm_prompt(event_title, other_person_email, time_period, duration, location, other_info, current_user_email)
            llm_response = get_llm_response(new_filename)
            if llm_response == "UNAVAILABLE":
                return "No time available!"
            #return llm_response
            llm_response = ast.literal_eval(llm_response)
            meeting_time_unparsed = llm_response['meeting time']
            num_of_mins_unparsed = llm_response['duration']
            #time_period_unparsed = int(llm_response['time period'])
            splitted = meeting_time_unparsed.split("T")
            date_unparsed = splitted[0]
            time_unparsed = splitted[1]
            #time_period_unparsed = int(splitted[2])
            #print("time period: next", time_period_unparsed,"hours")
            splitted_date = date_unparsed.split("-")
            year,month,date = int(splitted_date[0]), int(splitted_date[1]), int(splitted_date[2])

            start_dt = datetime.datetime.fromisoformat(meeting_time_unparsed)
            end_dt = start_dt + datetime.timedelta(minutes=int(float(num_of_mins_unparsed)))
            event_result = create_event(
                summary=event_title,
                start_datetime=start_dt.isoformat(),
                end_datetime=end_dt.isoformat(),
                location=location,
                attendees=[other_person_email]
            )

            return f"Success! Your meeting time is on {month}/{date}/{year} at {time_unparsed}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    return "Please submit the form to run the LLM"

@app.route('/connect_google')
def connect_google():
    if request.method == "POST":
        time_period = request.form.get("time_period")
        duration = request.form.get("duration")
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    service = build('calendar', 'v3', credentials=creds)
    
    # Get user's email
    user_info = service.about().get(fields='user').execute()
    user_email = user_info['user']['email']
    
    # Store user email in session
    session['current_user_email'] = user_email
    
    # Get calendar events
    now = datetime.datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + datetime.timedelta(days=7)).isoformat() + 'Z'  # Extended to 7 days
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime',
        maxResults=50
    ).execute()
    events = events_result.get('items', [])
    
    # Store user and events in database
    conn = sqlite3.connect('calendar_data.db')
    cursor = conn.cursor()
    
    # Insert or update user
    cursor.execute('''
        INSERT OR REPLACE INTO users (email, last_updated) 
        VALUES (?, CURRENT_TIMESTAMP)
    ''', (user_email,))
    
    # Clear existing events for this user
    cursor.execute('DELETE FROM events WHERE user_email = ?', (user_email,))
    
    # Insert new events
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        summary = event.get('summary', 'No Title')
        event_id = event.get('id', '')
        
        cursor.execute('''
            INSERT INTO events (user_email, event_id, summary, start_time, end_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_email, event_id, summary, start, end))
    
    conn.commit()
    conn.close()
    
    if not events:
        print(f"No upcoming events for {user_email} in the next 7 days.")
    else:
        print(f"Stored {len(events)} events for {user_email}")
    
    result = form()
    return result

def create_event(summary, start_datetime, end_datetime, location=None, attendees=None):
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': summary,
        'location': location if location else '',
        'start': {
            'dateTime': start_datetime,
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': 'America/New_York',
        },
        'attendees': [{'email': email} for email in (attendees or [])],
    }

    event_result = service.events().insert(calendarId='primary', body=event).execute()
    return event_result

if __name__ == '__main__':
    app.run(debug=True)