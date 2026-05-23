from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from brain import Brain
import uvicorn
import os
import psutil
import time

app = FastAPI()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Brain (no voice engine needed as client handles it)
brain = Brain()

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("text", "")
    
    if not user_input:
        return {"response": "I didn't catch that, Mr Aryan."}
    
    # Process with Brain
    response_text = await brain.think(user_input)
    
    return {"response": response_text}

@app.get("/history")
async def get_history():
    history = brain.memory.get_recent_history()
    return {"history": history}

@app.get("/stats")
async def get_stats():
    """Returns real-time system diagnostics."""
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    # Simple network speed estimation (bytes sent/received)
    net_io = psutil.net_io_counters()
    net_total = (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024 # MB
    
    return {
        "cpu": cpu,
        "ram": ram,
        "network": round(net_total, 2),
        "uptime": round(time.time() - os.path.getmtime(__file__), 0) # Mock uptime since server start
    }

# Serve static files (HTML, CSS, JS)
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    print("--- JARVIS Web Server Starting on http://localhost:8000 ---")
    uvicorn.run(app, host="0.0.0.0", port=8000)
