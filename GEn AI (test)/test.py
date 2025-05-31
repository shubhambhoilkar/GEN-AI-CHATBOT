'''from database import fetch_available_slots

print(fetch_available_slots())
'''

from pymongo import MongoClient
from datetime import datetime, timezone

client = MongoClient("mongodb://localhost:27017/")
db = client["CALL_REQUEST_DB"]
collection = db["call_requests"]

# Insert a sample document
call_request = {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+911234567890",
    "preferred_date": "2025-06-02",
    "status": "pending",
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc)
}

collection.insert_one(call_request)
