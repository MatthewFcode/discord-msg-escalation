## Discord Message Escalation AI - 24/7 daemon 

I built this project due to the fact that I am in too many discord channels and I can't always read all the messages that come through them. This project reads messages from my  discrod channells and forwards any important messages that I may miss directly to my gmail.

## Architecture

[ Discord Server ] 
       |
       | (on_message)
       v
[ Bot Service (bot.py) ] ----> [ FastAPI Gateway (main.py) ]
                                          |
                                          | (Auth + Pydantic Check)
                                          v
[ Langfuse (Tracing) ] <---- [ Escalation Logic (escalation.py) ]
                                          |
                                          | (NZ Time Conversion)
                                          v
[ Resend (Email) ] <---------- [ Gemini Flash LLM ]

## Stack

I went with a decoupled architecture to keep the bot light and the logic centralized.

* **Discord Bot** Built with `discord.py`. Its only job is to listen and forward payloads to the backend.
* **API Layer** `FastAPI` + `Pydantic`. Handles data validation and acts as the gatekeeper using secret header authentication.
* **Brain (LLM)** `LangChain` orchestration using `Google Gemini Flash`. It’s fast, efficient, and handles tool-calling natively.
* **Observability** `Langfuse`. Essential for tracing AI calls, checking latency, and seeing exactly why the model decided to (or not to) escalate.
* **Delivery** `Resend`. The specific tool the AI calls when it needs to fire off an email.
* **Testing** `Pytest` with `unittest.mock`. All external dependencies (Gemini, Resend, Langfuse) are mocked so CI stays fast and free.

## Architectural Flow

1. **Capture** The Discord bot listens for messages. It ignores its own messages to avoid loops and bundles metadata (author, channel, timestamp) into a JSON payload.
2. **Transport** The bot sends a `POST` request to the FastAPI backend with a custom `x-secret` header.
3. **Process** * FastAPI validates the secret and parses the data.
    * The timestamp is converted from UTC to **Pacific/Auckland** time to give the AI local context on when a message was sent.
    * A **Langfuse trace** is initialized to monitor the execution.
4. **Analyze** The message is sent to Gemini Flash. The system prompt instructs the model to only escalate "important" messages.
5. **Action** If Gemini triggers the `send_escalation_email` tool, the backend dispatches the email via Resend and logs the success back to the trace.

## CI/CD pipeline

I'm using GitHub Actions to maintain stability. Every push or PR to `main` triggers the **Test** workflow
* **Environment** Ubuntu-latest with Python 3.12.
* **Validation** It runs `pytest` against the FastAPI layer. 
* **Reliability** By mocking `sys.modules`, I can run tests without needing the actual AI keys present in the environment, ensuring the logic is sound even when external services are "offline."

### Current Production State
The system is currently running on **Dokku** across two containers: `web` (FastAPI) and `bot` (Discord listener). 


* **Monitoring** Langfuse is successfully capturing latency and tool arguments, providing a full audit trail of every escalation.
