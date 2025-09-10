from flask import Flask, render_template, request
import sys
import os
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
            
            return f"Success! LLM Response: {llm_response}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    return "Please submit the form to run the LLM"

if __name__ == '__main__':
    app.run(debug = True)