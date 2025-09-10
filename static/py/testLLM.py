sample_calendars = {
    "anmolkaranva@gmail.com": "Busy from 9:00am-10:30am, 1:00pm-2:00pm.",
    "pratyushsaxena4@gmail.com": "Busy from 10:00am-12:00pm, 2:30pm-3:30pm."
}

def get_user_inputs():
    thing_to_do = input("What do you want to do? (e.g. meet with someone, etc.)")
    person_to_meet_with = input("Enter the email of the person you want to meet with: ")
    time_period = input("What time period would you like to meet with them? (e.g. in the next 3 days, etc.)")
    duration = input("How long would you like to meet with them? (e.g. 30 minutes, 1 hour, etc.)")
    misc = input("Any other information you want to add? (e.g. location, etc.)")
    return thing_to_do, person_to_meet_with, time_period, duration, misc

def write_llm_prompt():
    thing_to_do, person_to_meet_with, time_period, duration, misc = get_user_inputs()
    
    f = open("")