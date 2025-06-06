import json
import openai
from logic import (
    request_call,
    fetch_available_slots,
    confirm_appointment_with_api,
    check_future_appointment,
    cancel_appointment
)
from demo_prompt import system_prompt, functions

#OpenAI GPT model number:gpt-3.5-turbo-1106
openai.api_key = "SECRET_KEY"

def validate_required(args, required_keys):
    print("validate:",args, required_keys)
    return [key for key in required_keys if key not in args or not args[key]]

def display_slots(slots):
    """Format and display available slots."""
    if not slots:
        return "❌ No available slots found."
    return "\n".join([f"📅 {date}: {', \n'.join(times)}" for date, times in slots.items()])

session_store = {}

def run_conversation(user_input):
    print("user_input: ",user_input)
    user_id= user_input["user_id"]
    session_id = user_input["user_id"]
    messages= user_input["text"]
    client_id = user_input["client_id"]
    src_lang =user_input["src_lang"]
    location =user_input["location"]

    country_code =location.get("country","")
    timezone = location.get("timezone","")
    
    if session_id not in session_store:
        session_store[session_id] = {
            "messages": [system_prompt],
            "user_data": {},
            "reschedule_flow": False
        }

    state = session_store[session_id]
    messages = state["messages"]
    user_data = state["user_data"]
    reschedule_flow = state["reschedule_flow"]

    messages.append({"role": "user", "content": user_input["text"]})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        user= user_id,
        functions=functions,
        function_call="auto"
    )
    
    msg = response["choices"][0]["message"]

    if msg.get("function_call"):
        fn_name = msg["function_call"]["name"]
        try:
            args = json.loads(msg["function_call"]["arguments"])
            print("args: ",args)
        except Exception as e:
            return f"⚠️ Failed to parse arguments: {e}"

        user_data.update(args)
        print("see use_data:",user_data)

        if fn_name == "get_available_slots":
            slots = fetch_available_slots()  # your existing data source
            formatted = display_slots(slots)
            messages.append({
                "role": "function",
                "name": fn_name,
                "content": formatted
            })
            return formatted


        elif fn_name == "book_appointment":
            required = ["name", "email", "phone"]
            missing = validate_required(user_data, required)

            if missing:
                messages.append({
                    "role": "function",
                    "name": fn_name,
                    "content": f"Missing: {', '.join(missing)}"
                })
                return f"Missing info: {', '.join(missing)}"

            has_future, existing_data = check_future_appointment(user_data["phone"])
            if has_future and not user_data.get("reschedule_flow"):
                return (
                    "📅 You already have an upcoming appointment on "
                    f"{existing_data['date']} at {existing_data['preferred_time']}.\n"
                )
            else:
                print("NO appointment in future")

            slots = fetch_available_slots()
            date, time = user_data["date"], user_data["preferred_time"]

            if date not in slots or time not in slots[date]:
                return f"❌ Slot not available.\nHere are available slots:\n{display_slots(slots)}"

            if user_data.get("reschedule_flow"):
                cancel_appointment(user_data["phone"])

            success, result = confirm_appointment_with_api(user_data, client_id, country_code, timezone)

            if success:
                return f"{result}\n🎉 Appointment confirmed and saved."
            else:
                return f"{result}\n❌ Confirmation with external API failed."
            
#--CANCELL APPOINTMENT
        elif fn_name == "cancel_appointment":
            required = ["phone", "date", "time"]
            missing = validate_required(user_data, required)

            if missing:
                messages.append({
                    "role": "function",
                    "name": fn_name,
                    "content": f"Missing: {', '.join(missing)}"
                })
                return f"Missing info: {', '.join(missing)}"

            phone = user_data["phone"]
            date = user_data["date"]
            time = user_data["time"]
            success, result = cancel_appointment(phone, date, time)

            if success:
                return f"✅ Your appointment on {date} at {time} for phone number {phone} has been successfully cancelled."
            else:
                error_detail = result.get("error", "Unknown error occurred.")
                return f"❌ Failed to cancel your appointment. Reason: {error_detail}"

#--REQUEST AND STORE CALL BACK
        elif fn_name == "request_call":
            required = ["name","phone", "region"]
            missing = validate_required(user_data, required)
            print(validate_required(user_data,required))
            if missing:
                messages.append({
                    "role": "function",
                    "name": fn_name,
                    "content": f"Missing: {', '.join(missing)}"
                })

                return f"Missing info: {', '.join(missing)}"
            phone = user_data["phone"]
            region =user_data["region"]
            name =user_data["name"]

            success, result = request_call(name, phone, region)
#            print(result)
            if success:
                return (f"✅ Call request confirmed for {name} in {region}.Our team will contact you at {phone} shortly.")
            else:
                return f"❌ Failed to request a callback."

    else:
        messages.append(msg)
        return msg["content"]
    
