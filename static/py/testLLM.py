import time
import shutil
import json

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

def get_current_time_nanoseconds():
    return str(time.time_ns())

def write_llm_prompt( thing_to_do, person_to_meet_with, time_period, duration, misc):
    
    current_time_nanoseconds = get_current_time_nanoseconds()
    
    source_file = "static/py/promptfile.txt"
    new_filename = "static/py/" + current_time_nanoseconds + "prompt.txt"
    shutil.copy2(source_file, new_filename)
    
    with open(new_filename, "a") as f:
        f.write(f"\n\nCALENDAR DATA:\n")
        f.write(json.dumps(sample_calendars, indent=2))
        
        f.write(f"\n\nUSER INPUTS:\n")
        f.write(f"Thing to do: {thing_to_do}\n")
        f.write(f"Person to meet with: {person_to_meet_with}\n")
        f.write(f"Time period: {time_period}\n")
        f.write(f"Duration: {duration}\n")
        f.write(f"Additional information: {misc}\n")
        f.write("\n\n\nIf you find a valid time slot that meets all constraints, respond ONLY with the start time in the exact format: YYYY-MM-DDTHH:MM:SS.")
        f.write("\nDo not include any other words, explanations, or introductory phrases like /'Here is a good time:/'")
        f.write("\nIf, after analyzing the calendars and constraints, you determine that no common time slot is available, respond ONLY with the word UNAVAILABLE.")
    f.close()


    print(f"Created new prompt file: {new_filename}")
    return new_filename


def get_llm_response(new_filename):
    with open(new_filename, "r") as f:
        prompt = f.read()
    
    
    #return prompt


def main():
   

    thing_to_do, person_to_meet_with, time_period, duration, misc = get_user_inputs()

    new_filename = write_llm_prompt(thing_to_do, person_to_meet_with, time_period, duration, misc)
    
    llm_response = get_llm_response(new_filename)
    


if __name__ == "__main__":
    main()
        
