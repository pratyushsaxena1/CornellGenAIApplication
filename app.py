from flask import Flask, render_template, request

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
    return event_title

if __name__ == '__main__':
    app.run(debug = True)