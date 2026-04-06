import asyncio
import os
import time 
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse.client import Langfuse 
from dotenv import load_dotenv

load_dotenv()

model = ChatGoogleGenerativeAI(
  model="models/gemini-flash-latest",
  temperature="0.7"
  api_key=os.environ["GOOGLE_API_KEY"]
)

#langfuse client 
langfuse = Langfuse (
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ["LANGFUSE_BASE_URL"],
)

def escalation_function(discord_message): 

  trace = langfuse.trace(
    name = 'dicord-escalation',
    discord_message = discord_message 
  )

  start_latency = time.time()

  messages = [
    SystemMessage(content=f"""You are a message escalation checker. Any important messages need to be escalated to Matthew."""), 
    HumanMessage(content=discord_message)
  ]
  
  end_latency = int((time.time() - start_latency) * 1000)

  result = model.invoke(messages)

  trace.update(
    output= result.content,
    metadata={"latency": end_latency}
  )
  
  langfuse.flush()







  