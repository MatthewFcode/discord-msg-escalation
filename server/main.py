import os
from fastapi import FastAPI, HTTPException, Header
from dotenv import load_dotenv
from pydantic import BaseModel # class from pydantic that validates data and parses JSON into python objects 
from escalation import escalation_function

load_dotenv()

app = FastAPI()
API_SECRET = os.getenv("API_SECRET")

class DiscordMessage(BaseModel): #validates request comes in this shape and parse the JSON object into python objects
    content: str
    author: str
    author_id: str
    channel: str
    channel_id: str
    guild: str
    guild_id: str
    timestamp: str


@app.post("/api/v1/bot")
async def escalation(data: DiscordMessage, x_secret: str = Header(None)):
    if x_secret != API_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    #calling the activation function
    result = escalation_function(data)
    print(result)



