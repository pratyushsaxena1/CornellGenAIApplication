from flask import Flask, render_template,request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
import sys
import ast
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'static', 'py'))
from testLLM import write_llm_prompt, get_llm_response


app = Flask(__name__)
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

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
            new_filename = write_llm_prompt(event_title, other_person_email, time_period, duration, location,other_info)
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
    now = datetime.datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    time_max = (now + datetime.timedelta(days=2)).isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime',
        maxResults=50
    ).execute()
    events = events_result.get('items', [])
    if not events:
        print("No upcoming events in the next 2 days.")
    else:
        print("Upcoming events in the next 2 days:")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event.get('summary', 'No Title'))
    result = form()
    return result

if __name__ == '__main__':
    app.run(debug=True)