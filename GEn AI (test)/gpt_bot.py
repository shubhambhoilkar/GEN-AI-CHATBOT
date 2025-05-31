import json
import openai
from logic import (
    book_slot,
    fetch_available_slots,
    request_call,
    confirm_appointment_with_api
)
from prompts import system_prompt, functions

# Load API key securely in production!
openai.api_key = "sk-proj-"

def validate_required(args, required_keys):
    """Check for any missing required fields."""
    return [key for key in required_keys if key not in args or not args[key]]

def display_slots(slots):
    """Format and display available slots."""
    if not slots:
        return "❌ No available slots found."
    return "\n".join([f"📅 {date}: {', '.join(times)}" for date, times in slots.items()])

def chat():
    print("🤖 GPT Customer Support Bot")
    print("Type 'exit' to quit\n")

    messages = [system_prompt]
    user_data = {}

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Bot: Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            messages=messages,
            functions=functions,
            function_call="auto"
        )

        msg = response["choices"][0]["message"]

        if msg.get("function_call"):
            fn_name = msg["function_call"]["name"]
            try:
                args = json.loads(msg["function_call"]["arguments"])
            except Exception as e:
                print("Bot: ⚠️ Failed to parse arguments:", e)
                continue

            user_data.update(args)

            if fn_name == "get_available_slots":
                slots = fetch_available_slots()
                formatted = display_slots(slots)
                print("Bot:", formatted)
                messages.append({
                    "role": "function",
                    "name": fn_name,
                    "content": formatted
                })

            elif fn_name == "book_appointment":
                required = ["name", "email", "phone", "company", "date", "preferred_time"]
                missing = validate_required(user_data, required)

                if missing:
                    print(f"Bot: Missing info: {', '.join(missing)}")
                    messages.append({
                        "role": "function",
                        "name": fn_name,
                        "content": f"Missing: {', '.join(missing)}"
                    })
                    continue

                # Step 1: Verify slot availability
                slots = fetch_available_slots()
                date, time = user_data["date"], user_data["preferred_time"]

                if date not in slots:
                    print(f"Bot: ❌ No slots available on {date}.")
                    print("Bot: Try one of these dates:")
                    print(display_slots(slots))
                    continue

                if time not in slots[date]:
                    print(f"Bot: ❌ '{time}' not available on {date}.")
                    print(f"Bot: Available times on {date}: {', '.join(slots[date])}")
                    continue

                # Step 2: Book appointment
                success, result = book_slot(date, time, user_data)
                print("Bot:", result)

                if success:
                    print("✅ DEBUG - Booking succeeded, proceeding to confirm API with data:")
                    print(user_data)
                    confirm_success, confirm_msg = confirm_appointment_with_api(user_data)
                    print("Bot:", confirm_msg)

                    if confirm_success:
                        print("Bot: 🎉 Appointment confirmed and saved.")
                        break
                    else:
                        print("Bot: ❌ Confirmation with external API failed.")
                        continue

            elif fn_name == "request_call":
                required = ["phone", "email", "date"]
                missing = validate_required(user_data, required)

                if missing:
                    print(f"Bot: Missing info: {', '.join(missing)}")
                    messages.append({
                        "role": "function",
                        "name": fn_name,
                        "content": f"Missing: {', '.join(missing)}"
                    })
                    continue

                success, result = request_call(user_data["date"], user_data["phone"], user_data["email"])
                print("Bot:", result)
                if success:
                    break

        else:
            print("Bot:", msg["content"])
            messages.append(msg)

if __name__ == "__main__":
    chat()
