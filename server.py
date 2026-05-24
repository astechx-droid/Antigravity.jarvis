from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import psutil
import time

from main import process_query

app = FastAPI(title="JARVIS")

_START_TIME = time.time()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():

    return {
        "status": "ok",
        "uptime": round(time.time() - _START_TIME, 0),
    }

@app.post("/chat")
async def chat(request: Request):

    data = await request.json()

    user_input = data.get("text", "")

    if not user_input:
        return {
            "response": "I didn't catch that, Mr Aryan."
        }

    try:

        response = await process_query(user_input)

        return {
            "response": response
        }

    except Exception as e:

        return {
            "response": f"Error: {str(e)}"
        }

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

# Static files
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )