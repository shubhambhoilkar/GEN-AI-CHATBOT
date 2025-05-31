import requests
from pymongo import MongoClient
SLOT_API_URL = "https://stgbot.genieus4u.ai/api/cb"

def fetch_available_slots():
    payload = {
        "route": "appointment_info",
        "client_app_key": "44ihRG38UX24DKeFzE15FbbPZfCgz3rh"
    }

    try:
        response = requests.post(SLOT_API_URL, json=payload)
        response.raise_for_status()

        data = response.json()
        formatted = {}
        for item in data.get("available_dates", []):
            date = item.get("date")
            slots = item.get("slots", [])
            if date and slots:
                formatted[date] = slots

        return formatted

    except requests.RequestException as e:
        print("❌ API request failed:", e)
        return {}
    except ValueError:
        print("❌ Failed to decode JSON")
        return {}
    
def get_mongo_client(uri= "mongodb://localhost:27017/"):
    return MongoClient(uri)

def get_call_request_collection():
    client = get_mongo_client()
    db = client["CALL_REQUEST_DB"]
    return db["call_requests"]