from fastapi import FastAPI
from pydantic import BaseModel
from gpt_bot import run_conversation

app = FastAPI()

class ChatInput(BaseModel):
    user_id: str
    text: str 
    src_lang: str 
    location: dict   
    client_id : str

@app.post("/chat")
def chat_endpoint(input: ChatInput):
    reply =run_conversation(input.dict())
    return {"response": reply}