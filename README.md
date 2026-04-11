### Discord Message Escalation AI - 24/7 daemon 
AI powered message triage and escalation system integrating real time event streams with sound LLM architecture.
I built this project due to the fact that I am in too many discord channels and I can't always read all the messages that come through them. This project reads messages from my  discrod channells and forwards any important messages that I may miss directly to my gmail.

### Architecture
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

### Stack
I went with a decoupled architecture to keep the bot light and the logic centralized.

* **Discord Bot** Built with `discord.py`. Its only job is to listen and forward payloads to the backend.
* **API Layer** `FastAPI` + `Pydantic`. Handles data validation and acts as the gatekeeper using secret header authentication.
* **Brain (LLM)** `LangChain` orchestration using `Google Gemini Flash`. It’s fast, efficient, and handles tool-calling natively.
* **Observability** `Langfuse`. Essential for tracing AI calls, checking latency, and seeing exactly why the model decided to (or not to) escalate.
* **Delivery** `Resend`. The specific tool the AI calls when it needs to fire off an email.
* **Testing** `Pytest` with `unittest.mock`. All external dependencies (Gemini, Resend, Langfuse) are mocked so CI stays fast and free.

### Architectural Flow
1. **Capture** The Discord bot listens for messages. It ignores its own messages to avoid loops and bundles metadata (author, channel, timestamp) into a JSON payload.
2. **Transport** The bot sends a `POST` request to the FastAPI backend with a custom `x-secret` header.
3. **Process** * FastAPI validates the secret and parses the data.
    * The timestamp is converted from UTC to **Pacific/Auckland** time to give the AI local context on when a message was sent.
    * A **Langfuse trace** is initialized to monitor the execution.
4. **Analyze** The message is sent to Gemini Flash. The system prompt instructs the model to only escalate "important" messages.
5. **Action** If Gemini triggers the `send_escalation_email` tool, the backend dispatches the email via Resend and logs the success back to the trace.

### CI/CD pipeline
I'm using GitHub Actions to maintain stability. Every push or PR to `main` triggers the **Test** workflow
* **Environment** Ubuntu-latest with Python 3.12.
* **Validation** It runs `pytest` against the FastAPI layer. 
* **Reliability** By mocking `sys.modules`, I can run tests without needing the actual AI keys present in the environment, ensuring the logic is sound even when external services are "offline."

### Current Production State
The system is currently running on **Dokku** across two containers: `web` (FastAPI) and `bot` (Discord listener). 

* **Monitoring** Langfuse is successfully capturing latency and tool arguments, providing a full audit trail of every escalation.

### The Road to Production
Getting this system live was more involved than the architecture diagram suggests. Here's what actually happened.
**It starts simply enough.** The two services `web` (FastAPI) and `bot` (Discord listener) — each have their own `Dockerfile`. Locally, they talk to each other over Docker's internal network without complaint. The bot hits the API, the AI thinks, an email fires. Done. Ship it.
**Then Dokku enters the picture.** Dokku runs each service as a separate app, which means two separate process containers, two separate internal hostnames, and critically a reverse proxy (nginx) sitting in front of everything handling TLS termination. What worked in local Docker Compose suddenly needed rethinking: the bot can't just `POST` to `localhost`; it needs to hit the FastAPI app's Dokku-assigned internal URL. Environment variables were wired up, the `GATEWAY_URL` updated, containers redeployed.

**Then the certificate issues started.** The proxy was terminating SSL at the edge and forwarding plain HTTP internally, which is fine until you're debugging and can't tell whether a connection failure is a networking problem, a cert problem, or the API actually returning a 4xx. The answer, as it usually is, was `dokku logs --tail` in one terminal and Langfuse traces in another: watch the raw stream for container-level errors, then cross-reference against the trace to see if the request even reached the LLM layer.

**The live log debugging loop looked like this:**
1. Deploy a change via `git push dokku main`
2. Tail the logs: `dokku logs <app> --tail`
3. Send a test message in Discord
4. Watch the request travel through the stack in real time
5. If it died, identify the layer: proxy? bot? API validation? LLM?
6. Fix, push, repeat

**Langfuse turned out to be essential here**, not just as an observability nicety but as a debugging tool. When a message made it past the API layer but the email never fired, the trace told us exactly what the model received, what it decided, and whether it tried to invoke `send_escalation_email` or concluded the message wasn't important enough. Without that, the silence between "message sent" and "no email received" would have been genuinely difficult to diagnose.

**Current state:** both containers are running as persistent daemons on the remote server. The bot wakes up on `on_message`, the API processes and traces every call, and the Gmail notifications arrive with correct NZ timestamps. The CI pipeline catches regressions before they reach the server. The system has been quietly doing its job ever since.