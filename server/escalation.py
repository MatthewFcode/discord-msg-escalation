import asyncio
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from sentence_transformers import SentenceTransformer
from langfuse.client import Langfuse 



load_dotenv()

def escalation_function(discord_message): 
