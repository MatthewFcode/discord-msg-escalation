import asyncio
import os
import time 
import resend
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse.client import Langfuse 
from dotenv import load_dotenv


load_dotenv()

model = ChatGoogleGenerativeAI(
  model="models/gemini-flash-latest",
  temperature="0.7",
  api_key=os.environ["GOOGLE_API_KEY"]
)

#langfuse client 
langfuse = Langfuse (
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ["LANGFUSE_BASE_URL"],
)

@tool
def send_escalation_email(subject: str, body: str): 
  #resend api key 
  resend.api_key = os.environ["RESEND_API_KEY"]

  r = resend.Emails.send({
    "from": "AI-Assistant <onboarding@resend.dev>", # Use your verified domain in prod
        "to": ["matthew@example.com"],
        "subject": subject,
        "html": f"<p>{body}</p>"
  })

  return f"Email sent successfully: {r['id']}"

def escalation_function(discord_message): 

  trace = langfuse.trace(
    name = 'dicord-escalation',
    discord_message = discord_message 
  )

  start_latency = time.time()

  tools = [send_escalation_email]

  model_with_tools = model.bind_tools(tools)

  messages = [
    SystemMessage(content=f"""You are a message escalation checker. Any important messages need to be escalated to Matthew."""), 
    HumanMessage(content=discord_message)
  ]
  
  

  result = model_with_tools.invoke(messages)

  if result.tool_calls:
        for tool_call in result.tool_calls:
            # This is where the magic happens:
            # We take the AI's suggested arguments and pass them to your Python function
            tool_output = send_escalation_email.invoke(tool_call["args"])
            print(f"Tool executed: {tool_output}")
            
            # Update trace with the tool activity
            trace.update(metadata={"tool_used": tool_call["name"], "tool_output": tool_output})

  end_latency = int((time.time() - start_latency) * 1000)

  trace.update(
    output= result.content,
    metadata={"latency": end_latency}
  )
  
  langfuse.flush()







  