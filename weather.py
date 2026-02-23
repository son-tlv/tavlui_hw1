from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
from datetime import datetime, timezone
import os

load_dotenv() 

app = Flask(__name__)
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY") 
SAAS_TOKEN = os.environ.get("SAAS_TOKEN") 
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route("/")
def home_page():
    return "<p><h2>Server running. Tavlui Sofiia</h2></p>"

@app.route('/api/weather', methods=['POST'])
def get_weather():
    data = request.json
    
    if not data:
        raise InvalidUsage("Invalid JSON payload", status_code=400)
        
    provided_token = data.get("token")
    if provided_token is None:
        raise InvalidUsage("Token is required", status_code=400)
    if provided_token != SAAS_TOKEN:
        raise InvalidUsage("Invalid token. Access denied.", status_code=403)

    location = data.get("location")
    date = data.get("date")

    if not location or not date:
        raise InvalidUsage("Location and date are required fields", status_code=400)
    
    vc_url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{date}"
    params = {"unitGroup": "metric", "key": WEATHER_API_KEY, "contentType": "json"}
    
    vc_response = requests.get(vc_url, params=params)
    
    if vc_response.status_code != 200:
        raise InvalidUsage(f"Visual Crossing API Error: {vc_response.text}", status_code=vc_response.status_code)

    vc_data = vc_response.json()
    days = vc_data.get('days')
    if not days or len(days) == 0:
        raise InvalidUsage("No weather data found", status_code=404)
        
    day_weather = days[0]
    temp = day_weather.get("temp")
    wind = day_weather.get("windspeed")
    
    prompt = f"The weather in {location} on {date} will be {temp}°C with {wind} kph wind. Give a single, short sentence suggesting what a student should wear."
    
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    gemini_payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        ai_req = requests.post(gemini_url, json=gemini_payload)
        ai_data = ai_req.json()
        ai_response = ai_data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        ai_response = "AI suggestion currently unavailable."

    response_payload = {
        "requester_name": data.get("requester_name"),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "location": location,
        "date": date,
        "weather": {
            "temp_c": temp,
            "wind_kph": wind,
            "pressure_mb": day_weather.get("pressure"),
            "humidity": day_weather.get("humidity")
        },
        "ai_clothing_suggestion": ai_response 
    }
    return jsonify(response_payload)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)