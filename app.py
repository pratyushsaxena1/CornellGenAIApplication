from flask import Flask, render_template, request
import sys
import os
import ast
sys.path.append(os.path.join(os.path.dirname(__file__), 'static', 'py'))
from testLLM import write_llm_prompt, get_llm_response

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

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
                return "hello!"
            #return llm_response
            llm_response = ast.literal_eval(llm_response)
            meeting_time_unparsed = llm_response['meeting time']
            num_of_mins_unparsed = llm_response['duration']
            splitted = meeting_time_unparsed.split("T")
            date_unparsed = splitted[0]
            time_unparsed = splitted[1]
            splitted_date = date_unparsed.split("-")
            year,month,date = int(splitted_date[0]), int(splitted_date[1]), int(splitted_date[2])


            return f"Success! Your meeting time is on {month}/{date}/{year} at {time_unparsed}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    return "Please submit the form to run the LLM"

if __name__ == '__main__':
    app.run(debug = True)