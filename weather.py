from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
from datetime import datetime, timezone
import os

load_dotenv() # Loads the .env file

app = Flask(__name__)
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY") 
SAAS_TOKEN = os.environ.get("SAAS_TOKEN") 

@app.route('/api/weather', methods=['POST'])
def get_weather():
    data = request.json
    provided_token = data.get("token")
    if provided_token != SAAS_TOKEN:
        return jsonify({"error": "Invalid token. Access denied."}), 401
    location = data.get("location")
    date = data.get("date")
    
    # Fetch Visual Crossing Data
    vc_url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/{date}"
    params = {"unitGroup": "metric", "key": WEATHER_API_KEY, "contentType": "json"}
    vc_response = requests.get(vc_url, params=params).json()
    day_weather = vc_response.get('days', [{}])[0]
    
    # Build the final response
    response_payload = {
        "requester_name": data.get("requester_name"),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "location": location,
        "date": date,
        "weather": {
            "temp_c": day_weather.get("temp"),
            "wind_kph": day_weather.get("windspeed"),
            "pressure_mb": day_weather.get("pressure"),
            "humidity": day_weather.get("humidity")
        }
    }
    return jsonify(response_payload)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
