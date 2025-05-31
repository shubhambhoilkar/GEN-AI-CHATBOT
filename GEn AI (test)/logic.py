import requests
from datetime import datetime, timezone 
from database import fetch_available_slots , get_call_request_collection

def book_slot(date, preferred_time, user_info):
    slots = fetch_available_slots()
    if date not in slots:
        return False, "❌ No slots available for selected date."

    available_times = slots[date]
    if preferred_time in available_times:
        # Optionally: call an API to mark the slot booked
        # Example: requests.post(...)

        return True, f"✅ Appointment booked for {date} at {preferred_time}."
    else:
        return False, f"❌ Time {preferred_time} not available on {date}."


def request_call(date, phone, email ,name=None):
    collection = get_call_request_collection()
    doc ={
        "name":name or "Unknown",
        "email":email,
        "phone":phone,
        "prefered_date": date,
        "status":"pending",
        "created_at":datetime.now(timezone.utc),
        "updated_at":datetime.now(timezone.utc)
    }

    collection.insert_one(doc)
    return True, "📞 Your callback request has been submitted. Our team will reach out on the preferred date."

'''def has_existing_call(phone):
    return any(call["phone"] == phone for call in CALL_REQUEST_DB)
'''
def confirm_appointment_with_api(user_data):
    url = "https://stgbot.genieus4u.ai/api/cb"
    headers={
        "Content-Type":"application/JSON"
    }
    payload ={
        "route": "process_data",
        "content_type": "appointment_confirmation",
        "client_id": "44ihRG38UX24DKeFzE15FbbPZfCgz3rh",
        "appointment_name": "send_notification_test_app_obj",
        "appointment_period": "",  # Optional if not used
        "appointment_time": user_data["preferred_time"],
        "appointment_date": user_data["date"],
        "appointment_email": user_data["email"],
        "appointment_phone_number": user_data["phone"],
        "appointment_country_id": "",
        "user_timezone": ""
    }
    try:
        response= requests.post(url, headers= headers,json=payload)
        if response.status_code ==200:
            return True, "✅ Appointment confirmed and stored successfully."
        else:
            return False, "❌ Failed to store appointment: {response.status_code}, {response.text}"
    except Exception as e:
        return False,  f"❌ Exception occurred: {str(e)}"
