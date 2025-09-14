import time
import shutil
import json
import datetime
import sqlite3
from google import genai
import pytz

# from flask import request


# if request.method == "POST":
#     event_title = request.form.get("event_title")    
#     print(event_title)




def get_user_inputs():
    thing_to_do = input("What do you want to do? (e.g. meet with someone, etc.)")
    person_to_meet_with = input("Enter the email of the person you want to meet with: ")
    time_period = input("What time period would you like to meet with them? (e.g. in the next 3 days, etc.)")
    duration = input("How long would you like to meet with them? (e.g. 30 minutes, 1 hour, etc.)")
    misc = input("Any other information you want to add? (e.g. location, etc.)")
    return thing_to_do, person_to_meet_with, time_period, duration, misc

def get_current_time_nanoseconds():
    return str(time.time_ns())

def get_calendar_data_from_db(person_to_meet_with):
    """Get calendar data from database for the specified person"""
    conn = sqlite3.connect('calendar_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT summary, start_time, end_time, calendar_id 
        FROM events 
        WHERE user_email = ?
        ORDER BY start_time
    ''', (person_to_meet_with,))
    
    events = cursor.fetchall()
    conn.close()
    
    if not events:
        return f"No calendar data found for {person_to_meet_with}"
    
    busy_times = []
    for summary, start_time, end_time, calendar_id in events:
        calendar_info = f" (from {calendar_id} calendar)" if calendar_id != 'primary' else ""
        busy_times.append(f"Busy from {start_time} to {end_time} - {summary}{calendar_info}")
    
    return f"{person_to_meet_with}: " + "; ".join(busy_times)

def write_llm_prompt( thing_to_do, person_to_meet_with, time_period, duration, location, misc, current_user_email=None):
    
    
 
    #google gemini first call to get the time period so we can give it to google calendar
    with open("static/py/apikey.txt", "r") as f:
        current_datetime_edt = datetime.datetime.now(pytz.timezone('America/New_York'))


        api_key = f.read().strip()
        timePdPrompt = f"The time period is {time_period}. The current time is {current_datetime_edt} . I want you to return the time period in number of hours. If the user says something like \'Today\' then the time period that you return should be the INTEGER number of hours from now until the end of the day. ONLY return a single number, no other text like \'Here is the number of hours\'.\nRemember, this is the real time period: {time_period}"
        client = genai.Client(api_key=api_key)
        timePdResponse = client.models.generate_content(
            model="gemini-2.5-flash", contents=timePdPrompt
        )
        timePdResponse = int(timePdResponse.text)
        print(timePdResponse)
    
    current_time_nanoseconds = get_current_time_nanoseconds()
    source_file = "static/py/promptfile.txt"
    new_filename = "static/promptfiles/" + current_time_nanoseconds + "prompt.txt"
    shutil.copy2(source_file, new_filename)

    other_person_calendar = get_calendar_data_from_db(person_to_meet_with)
    
    current_user_calendar = ""
    if current_user_email:
        current_user_calendar = get_calendar_data_from_db(current_user_email)
    
    calendar_data = f"{other_person_calendar}\n\n{current_user_calendar}" if current_user_calendar else other_person_calendar



    with open(new_filename, "a") as f:
        
        f.write("\n\n")
        f.write(f"\n\nCALENDAR DATA:\n")
        f.write(calendar_data)
        
        f.write(f"\n\nUSER INPUTS:\n")
        f.write(f"Thing to do: {thing_to_do}\n")
        f.write(f"Person to meet with: {person_to_meet_with}\n")
        f.write(f"Time period (in what time period the meeting has to take place): {time_period}\n")
        f.write(f"Duration: {duration}\n")
        f.write(f"Location: {location}\n")
        f.write(f"Additional information: {misc}\n")

        f.write("\n\n")
       
        f.write("\n\n\nIf you find a valid time slot that meets all constraints, respond ONLY with the start time in the exact format: {'meeting time':'YYYY-MM-DDTHH:MM:SS','duration': 'NUMBEROFMINUTES'}. Every key and value should be a string, even if it is a number.")
        f.write("\nDo not include any other words, explanations, or introductory phrases like /'Here is a good time:/'")
        f.write("\nIf, after analyzing the calendars and constraints, you determine that no common time slot is available, respond ONLY with the word UNAVAILABLE.")
        current_datetime_edt = datetime.datetime.now(pytz.timezone('America/New_York'))

        f.write(f"\n\nThe current time is {current_datetime_edt}. You should only look at events within the given time period.")# When you return the time period in number of hours, consider eastern time rather than UTC. If the user says something like \'Today\' then the time period that you return should be the INTEGER number of hours from now until the end of the day. ")
        #f.write("Remember that the meeting time is not the current time. The meeting time is the time I would like you to schedule the meeting for. the current time is solely used for helping you calculate time period.")

        f.write("\nLeave at least a 15-minute buffer before and after other events so that people can easily get from one event to this scheduled event. \nPlease give preference to reasonable times. For example, you shouldn't schedule an event for the middle of the night unless there's no other option.\nTake the event title into account, and determine what would be a good time for that event.")
    f.close()


    print(f"Created new prompt file: {new_filename}")
    return new_filename


def get_llm_response(new_filename):
    with open("static/py/apikey.txt", "r") as f:
        api_key = f.read().strip()
    
    with open(new_filename, "r") as f:
        prompt = f.read()
    
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    return (response.text)

    # print(f"API Key loaded: {api_key[:5]}...")  
    # print(f"Prompt loaded from: {new_filename}")
    
    #return prompt


def main():
   

    thing_to_do, person_to_meet_with, time_period, duration, misc = get_user_inputs()

    new_filename = write_llm_prompt(thing_to_do, person_to_meet_with, time_period, duration, misc)
    
    llm_response = get_llm_response(new_filename)
    


if __name__ == "__main__":
    main()
        
