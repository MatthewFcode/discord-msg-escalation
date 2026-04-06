from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel # class from pydantic that validates data and parses JSON into python objects 
from escalation import escalation_function

app = FastAPI()

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
async def escalation(data: DiscordMessage):
    result = escalation_function(data)
    print(result)



