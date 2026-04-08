import asyncio
import os
import time 
import resend
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse.client import Langfuse 
from datetime import datetime
from zoneinfo import ZoneInfo
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
  """Send an email to Matthew detailing the message"""
  resend.api_key = os.environ["RESEND_API_KEY"]

  r = resend.Emails.send({
    "from": "Discord AI <onboarding@resend.dev>", # Use your verified domain in prod
        "to": ["matthewfoley333@gmail.com"],
        "subject": subject,
        "html": f"<p>{body}</p>"
  })

  return f"Email sent successfully: {r['id']}"

#AI escalation function 
def escalation_function(discord_message): 
  utc_time = datetime.fromisoformat(discord_message.timestamp)
  nz_time = utc_time.astimezone(ZoneInfo("Pacific/Auckland"))

  formatted_time = nz_time.strftime("%Y-%m-%d %H:%M:%S")


  trace = langfuse.trace(
    name = 'dicord-escalation',
    discord_message = discord_message.content
  )

  start_latency = time.time()

  tools = [send_escalation_email]

  model_with_tools = model.bind_tools(tools)

  messages = [
    SystemMessage(content=f"""You are a message escalation checker.
Only escalate messages that are important.
If not important, do nothing and return a message saying 'No escalation needed'."""), 
    HumanMessage(content=f"""Discord message received: 
                 Content: {discord_message.content}
                 Author: {discord_message.author}
                 Channel: {discord_message.channel}
                 Server: {discord_message.guild}
                 Time sent: {formatted_time}""")
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







  