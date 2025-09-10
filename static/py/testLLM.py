import time
import shutil
import json
import datetime
from google import genai
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

def write_llm_prompt( thing_to_do, person_to_meet_with, time_period, duration,location, misc):
    
    

    #google gemini first call to get the time period so we can give it to google calendar
    with open("static/py/apikey.txt", "r") as f:
        currTime = datetime.datetime.utcnow()

        api_key = f.read().strip()
        timePdPrompt = f"The time period is {time_period}. The current time is {currTime} (UTC). I want you to return the time period in number of hours, consider eastern time rather than UTC. If the user says something like \'Today\' then the time period that you return should be the INTEGER number of hours from now until the end of the day. ONLY return a single number, no other text like \'Here is the number of hours\'"
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

    sample_calendars = {
        "anmolkaranva@gmail.com": "Busy from 9:00am-10:30am, 1:00pm-2:00pm.",
        "pratyushsaxena4@gmail.com": "Busy from 10:00am-12:00pm, 2:30pm-3:30pm."
    }



    with open(new_filename, "a") as f:
        
        f.write("\n\n")
        f.write(f"\n\nCALENDAR DATA:\n")
        f.write(json.dumps(sample_calendars, indent=2))
        
        f.write(f"\n\nUSER INPUTS:\n")
        f.write(f"Thing to do: {thing_to_do}\n")
        f.write(f"Person to meet with: {person_to_meet_with}\n")
        f.write(f"Time period: {time_period}\n")
        f.write(f"Duration: {duration}\n")
        f.write(f"Location: {location}\n")
        f.write(f"Additional information: {misc}\n")

        f.write("\n\n")
       
        f.write("\n\n\nIf you find a valid time slot that meets all constraints, respond ONLY with the start time in the exact format: {'meeting time':'YYYY-MM-DDTHH:MM:SS','duration': 'NUMBEROFMINUTES'}. Every key and value should be a string, even if it is a number.")
        f.write("\nDo not include any other words, explanations, or introductory phrases like /'Here is a good time:/'")
        f.write("\nIf, after analyzing the calendars and constraints, you determine that no common time slot is available, respond ONLY with the word UNAVAILABLE.")
   
        f.write(f"The current time is {currTime} (UTC).")# When you return the time period in number of hours, consider eastern time rather than UTC. If the user says something like \'Today\' then the time period that you return should be the INTEGER number of hours from now until the end of the day. ")
        #f.write("Remember that the meeting time is not the current time. The meeting time is the time I would like you to schedule the meeting for. the current time is solely used for helping you calculate time period.")

        f.write("Leave at least a 15-minute buffer before and after other events so that people can easily get from one event to this scheduled event.")
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
        
