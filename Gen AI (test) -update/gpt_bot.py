import json
import openai
from collections import defaultdict
from logic import (
    book_slot,
    request_call,
    fetch_available_slots,
    confirm_appointment_with_api,
    check_future_appointment,
    cancel_appointment
)
from prompts import system_prompt, functions

#OpenAI GPT model number:gpt-3.5-turbo-1106
#openai.api_key = "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"

def validate_required(args, required_keys):
    """Check for any missing required fields."""
    return [key for key in required_keys if key not in args or not args[key]]

def display_slots(slots):
    """
    Formats available appointment slots grouped by date.
    Supports both list[dict] and dict[date] = [times] formats.
    """
    from collections import defaultdict

    if not slots:
        return "❌ No available slots found."

    grouped = defaultdict(list)

    # Auto-detect if slots is a dict already (date -> [times])
    if isinstance(slots, dict):
        grouped.update(slots)

    elif isinstance(slots, list):
        # Expecting list of dicts with 'date' and 'time'
        for slot in slots:
            if isinstance(slot, str):
                import json
                try:
                    slot = json.loads(slot)
                except json.JSONDecodeError:
                    continue
            if isinstance(slot, dict) and "date" in slot and "time" in slot:
                grouped[slot["date"]].append(slot["time"])

    if not grouped:
        return "❌ No valid slot data to display."

    output = []
    for date in sorted(grouped):
        output.append(f"📅 Date: {date}")
        for time in sorted(grouped[date]):
            output.append(f"   • {time}")
        output.append("")  # line break between dates

    return "\n".join(output)
        
session_store = {}

def run_conversation(user_input):
    user_id= user_input["user_id"]
    session_id = user_input["user_id"]
    messages= user_input["text"]
    client_id = user_input["client_id"]
    src_lang =user_input["src_lang"]
    location =user_input["location"]

    if session_id not in session_store:
        session_store[session_id] = {
            "messages": [system_prompt],
            "user_data": {},
            "reschedule_flow": False
        }

    state = session_store[session_id]
    messages = state["messages"]
#    print(messages)
    user_data = state["user_data"]
    reschedule_flow = state["reschedule_flow"]

    messages.append({"role": "user", "content": user_input["text"]})

    response = openai.ChatCompletion.create(
        model="gpt-4",
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
        except Exception as e:
            return f"⚠️ Failed to parse arguments: {e}"

        user_data.update(args)

        if fn_name == "get_available_slots":
            slots = fetch_available_slots()  # your existing data source
            formatted = display_slots(slots)
#            print("Bot:", formatted)
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
                    "Would you like to reschedule it? Reply with 'yes' or 'no'."
                )

            if has_future and user_input.strip().lower() == "yes":
                user_data["reschedule_flow"] = True
                return (
                    "What would you like to change? Reply with:\n"
                    "- 'date' to pick a new date\n"
                    "- 'time' to pick a new time for the existing date"
                )

            if user_data.get("reschedule_flow"):
                if user_input.strip().lower() == "date":
                    slots = fetch_available_slots()
                    return f"📅 Here are available slots:\n{display_slots(slots)}\nPlease provide your new date and time."

                elif user_input.strip().lower() == "time":
                    if "date" not in user_data:
                        return "❗ You need to select the date first before changing time."
                    slots = fetch_available_slots()
                    selected_date = user_data["date"]
                    if selected_date in slots:
                        return (
                            f"🕑 Available times for {selected_date}: "
                            f"{', '.join(slots[selected_date])}\nPlease enter your preferred time."
                        )
                    else:
                        return f"❌ No available slots for {selected_date}. Please choose another date."

            if "date" not in user_data or "preferred_time" not in user_data:
                return "❗ Please provide both date and time for your appointment."

            slots = fetch_available_slots()
            date, time = user_data["date"], user_data["preferred_time"]

            if date not in slots or time not in slots[date]:
                return f"❌ Slot not available.\nHere are available slots:\n{display_slots(slots)}"

            if user_data.get("reschedule_flow"):
                cancel_appointment(user_data["phone"])

            success, result = book_slot(date, time, user_data)
            messages.append({
                "role": "function",
                "name": fn_name,
                "content": result
            })

            if success:
                confirm_success = confirm_appointment_with_api(user_data,client_id=client_id,location=location)
                if confirm_success:
                    return f"{result}\n🎉 Appointment confirmed and saved."
                else:
                    return f"{result}\n❌ Confirmation with external API failed."
            return result

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
            required = ["phone", "name","region"]
            missing = validate_required(user_data, required)

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

            success, result = request_call(phone, region,name)

            if success:
                return (f"✅ Call request confirmed for {name} in {region}.Our team will contact you at {phone} shortly.")
            else:
                return f"❌ Failed to request a callback."

    else:
        messages.append(msg)
        return msg["content"]
    