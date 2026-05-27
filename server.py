from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from brain import Brain
from config import OPENROUTER_API_KEY

import uvicorn
import os
import psutil
import time

app = FastAPI(title="JARVIS")

_START_TIME = time.time()

# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# INIT BRAIN
# ---------------------------------------------------------

brain = Brain()

# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

@app.get("/health")
async def health():

    key_ok = bool(
        OPENROUTER_API_KEY and
        "your_key" not in OPENROUTER_API_KEY
    )

    return {
        "status": "ok" if key_ok else "missing_api_key",
        "openrouter": key_ok,
        "uptime": round(time.time() - _START_TIME, 0),
    }

# ---------------------------------------------------------
# CHAT
# ---------------------------------------------------------

@app.post("/chat")
async def chat(request: Request):

    data = await request.json()

    user_input = data.get("text", "")

    if not user_input:
        return {
            "response": "I didn't catch that, Mr Aryan."
        }

    if not OPENROUTER_API_KEY:

        return {
            "response": "OpenRouter API key missing on server."
        }

    try:

        response_text = await brain.think(user_input)

        return {
            "response": response_text
        }

    except Exception as e:

        return {
            "response": f"Server Error: {str(e)}"
        }

# ---------------------------------------------------------
# HISTORY
# ---------------------------------------------------------

@app.get("/history")
async def get_history():

    history = brain.memory.get_recent_history()

    return {
        "history": history
    }

# ---------------------------------------------------------
# STATS
# ---------------------------------------------------------

@app.get("/stats")
async def get_stats():

    cpu = psutil.cpu_percent(interval=None)

    ram = psutil.virtual_memory().percent

    net_io = psutil.net_io_counters()

    net_total = (
        net_io.bytes_sent +
        net_io.bytes_recv
    ) / 1024 / 1024

    return {
        "cpu": cpu,
        "ram": ram,
        "network": round(net_total, 2),
        "uptime": round(time.time() - _START_TIME, 0),
    }

# ---------------------------------------------------------
# STATIC FILES
# ---------------------------------------------------------

app.mount(
    "/",
    StaticFiles(directory=".", html=True),
    name="static"
)

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
