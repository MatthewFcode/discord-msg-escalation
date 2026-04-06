# bot.py
import discord
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
API_SECRET = os.getenv("API_SECRET")
API_URL = "http://localhost:8000/messages"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user} — watching {len(client.guilds)} server(s)")

@client.event
async def on_message(message):
    # Ignore the bot's own messages
    if message.author == client.user:
        return

    payload = {
        "content": message.content,
        "author": str(message.author.display_name),
        "author_id": str(message.author.id),
        "channel": str(message.channel.name),
        "channel_id": str(message.channel.id),
        "guild": str(message.guild.name) if message.guild else "DM",
        "guild_id": str(message.guild.id) if message.guild else "0",
        "timestamp": message.created_at.isoformat(),
    }

    try:
        async with httpx.AsyncClient() as http:
            response = await http.post(
                API_URL,
                json=payload,
                headers={"x-secret": API_SECRET},
                timeout=5.0
            )
            response.raise_for_status()
    except Exception as e:
        print(f"Failed to forward message: {e}")

client.run(DISCORD_TOKEN)