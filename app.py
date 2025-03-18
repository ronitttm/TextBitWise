import eventlet
eventlet.monkey_patch()

import os
import requests
from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback_secret_key")

# Initialize Flask-SocketIO
socketio = SocketIO(app, async_mode='eventlet')


# Hugging Face API details
API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
HEADERS = {"Authorization": f"Bearer {os.getenv('HF_API_KEY', '')}"}

# Flask-WTForms form
class TextSummarizationForm(FlaskForm):
    text = TextAreaField("Enter your text", validators=[DataRequired()])
    submit = SubmitField("Summarize")

# Function to query the Hugging Face API
def query(payload):
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()[0].get("summary_text", "Error: No summary returned.")
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

@app.route("/", methods=["GET", "POST"])
def home():
    form = TextSummarizationForm()
    return render_template("index.html", form=form)

@app.route('/about')
def about():
    return render_template('about.html') 

@app.route('/contact')
def contact():
    return render_template('contact.html') 

@socketio.on("summarize_text")
def handle_text_summarization(data):
    """Handles real-time summarization requests."""
    text = data.get("text", "").strip()
    if not text:
        emit("summary_response", {"summary": "Please enter text to summarize."})
        return
    
    summary = query({"inputs": text})
    emit("summary_response", {"summary": summary})

if __name__ == "__main__":
    socketio.run(app, debug=True)
