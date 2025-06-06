import requests
from datetime import datetime, timezone 

API_URL ="https://stgbot.genieus4u.ai/api/cb"
CLIENT_APP_KEY ="44ihRG38UX24DKeFzE15FbbPZfCgz3rh"

#Fetching available slots
def fetch_available_slots():
    payload = {
        "route": "appointment_info",
        "client_app_key": "44ihRG38UX24DKeFzE15FbbPZfCgz3rh"
    }

    try:
        response = requests.post(API_URL, json=payload)
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

#getting dates in button format
def get_available_dates_button_format(slots_dict):
    return [{"label": date, "intent": date} for date in slots_dict.keys()]

def get_time_slots_button_format(time_slots):
    return [{"label": t, "intent": t} for t in time_slots]


def get_time_period(time_str):
    time_obj = datetime.strptime(time_str.strip(), "%I:%M %p")
    hour = time_obj.hour
    if 0 <= hour < 12:
        return "morning"
    elif 12<= hour < 17:
        return "afternoon"
    else:
        return "evening"

# Adding User details to book appointment
def confirm_appointment_with_api(user_data, client_id, country_code, timezone):
    time_period = get_time_period(user_data["preferred_time"])
    url = "https://stgbot.genieus4u.ai/api/cb"
    headers={
        "Content-Type":"application/JSON"
    }
    payload ={
        "route": "process_data",
        "content_type": "appointment_confirmation",
        "client_id": client_id,
        "appointment_name": "send_notification_test_app_obj",
        "appointment_period": time_period,
        "appointment_time": user_data["preferred_time"],
        "appointment_date": user_data["date"],
        "appointment_email": user_data["email"],
        "appointment_phone_number": user_data["phone"],
        "appointment_country_id": country_code,
        "user_timezone": timezone
    }
    try:
        response= requests.post(url, headers= headers,json=payload)
        if response.status_code ==200:
            return True, "✅ Appointment confirmed and stored successfully."
        else:
            return False, f"❌ Failed to store appointment: {response.status_code}, {response.text}"
    except Exception as e:
        return False,  f"❌ Exception occurred: {str(e)}"

# Check if a user has a future appointment.
def check_future_appointment(phone):
    print("Future appointment function:", phone)
    url = "https://stgbot.genieus4u.ai/api/cb"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "client_app_key": "44ihRG38UX24DKeFzE15FbbPZfCgz3rh",  
        "user_id": phone,
        "route": "future_appointment"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success" and data.get("has_appointment"):
            return True, "You are already having appointment."
        return False, "Future appointment not found."

    except requests.RequestException as e:
        print("❌ Error checking future appointment:", e)
        return False, {"error": str(e)}

#Cancell Appoinment
def cancel_appointment(phone,date,time):
    url = API_URL 
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
            "client_id":CLIENT_APP_KEY,
            "route":"cancel_appointment",
            "user_id": phone,
            "appointment_date": date,
            "appointment_period": "",  
            "appointment_time": time }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return True, "Thank You for the paitence, your appointment cancelled successfully."
        else:
            return False, f"Oops, Failed to cancel appointment. Status code: {response.status_code}"
    except Exception as e:
        return False, f"Error during cancellation: {str(e)}"

#Check if a user has a future callback scheduled.
def check_future_callback(user_id):
    url = API_URL
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "client_app_key": CLIENT_APP_KEY,
        "user_id": user_id,
        "route": "future_callback"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success" and data.get("has_callback"):
            return True, data
        return False, data

    except requests.RequestException as e:
        print("❌ Error checking future callback:", e)
        return False, {"error": str(e)}


# Getting exiting Call request for user from phone number identifucation
def get_existing_call_requests(phone):
    url = API_URL
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
    "client_app_key": CLIENT_APP_KEY,
    "user_id":phone,
    "route":"future_callback"
}
    try:
        response= requests.post(url, headers= headers,json=payload)
        if response.status_code ==200:
            return True, "✅ Your Call request is on board. Our team will call you shortly."
        else:
            return False, f"❌ We don't have any Call request for you. Would you like to book a call request. {request_call}"
    except Exception as e:
        return False,  f"❌ Exception occurred: {str(e)}"

def request_call(name, phone, region):
    print("request call function:",name, phone, region)
    url = API_URL
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
            "client_id":"44ihRG38UX24DKeFzE15FbbPZfCgz3rh",
            "user_timezone":"Asia/Kolkata",
            "callback_name":name,
            "callback_phone":phone,
            "callback_region":region,
            "route":"process_callback_data"
        }
    response= requests.post(url, headers= headers,json=payload)
    if response.status_code ==200:
        return True, "✅ Your Call request is Confirmed. Our team will call you accordingly."
    else:
        return False, f"❌ Unable to book a call request. Please try once again {request_call}"