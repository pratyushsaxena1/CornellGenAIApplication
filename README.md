# Creavent

Submitted as an application to Cornell University's Generative AI Club. 

* Project Demo: https://www.youtube.com
* Project Website: https://creavent.onrender.com/

Creavent is a personalized meeting scheduler that examines the Google Calendars of the user, along with the people the user would like to meet with, and creates a Google Calendar event on behalf of the user. This can save time and back-and-forth communication between people for scheduling, automating the scheduling process and finding a time that works for everyone.

Creavent is built using a Python and Flask backend. It has a lightweight web server and core logic for routing, authentication, and rendering web pages. The project integrates Google OAuth for secure login and Google Calendar API access, which allows it to interact with users’ calendar events for scheduling and coordination. At its core, Creavent uses generative AI models from OpenAI (GPT-5) and Google Gemini to interpret natural language scheduling requests and automate event planning. Local data persistence is handled through SQLite, reducing redundant API calls and providing efficient database access. The frontend leverages HTML, CSS, and Jinja2 templating to deliver a responsive user interface, while supporting libraries like python-dotenv, requests, and httpx facilitate environment management and robust API communication. This combination of technologies allows Creavent to automate complex meeting scheduling and event management.
