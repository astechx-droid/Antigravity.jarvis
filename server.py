from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import edge_tts
import os
from uuid import uuid4

# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI()

# =====================================================
# CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# STATIC FOLDER
# =====================================================

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

# =====================================================
# ROOT
# =====================================================

@app.get("/")
async def root():
    return {
        "status": "Jarvis server online"
    }

# =====================================================
# STATS API
# =====================================================

@app.get("/stats")
async def stats():
    return {
        "status": "online",
        "assistant": "Jarvis",
        "version": "2.0",
        "voice": "active",
        "render": "working"
    }

# =====================================================
# TTS API
# =====================================================

@app.post("/api/tts")
async def tts(request: Request):

    try:

        data = await request.json()

        text = data.get("text", "").strip()

        if not text:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "No text provided"
                }
            )

        # =================================================
        # HINDI / ENGLISH VOICE DETECTION
        # =================================================

        hindi_words = [
            "hai",
            "kya",
            "kaise",
            "mera",
            "bhai",
            "yaar",
            "tum",
            "main",
            "kar",
            "acha",
            "haan",
            "nahi",
            "jarvis"
        ]

        lower = text.lower()

        if any(word in lower for word in hindi_words):
            voice = "hi-IN-MadhurNeural"
        else:
            voice = "en-IN-PrabhatNeural"

        # =================================================
        # GENERATE MP3
        # =================================================

        filename = f"{uuid4()}.mp3"

        filepath = os.path.join(
            "static",
            filename
        )

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate="+10%",
            pitch="+0Hz"
        )

        await communicate.save(filepath)

        return {
            "success": True,
            "audio_url": f"/static/{filename}",
            "voice": voice
        }

    except Exception as e:

        print("\n[TTS ERROR]")
        print(str(e))

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

# =====================================================
# CHAT API
# =====================================================

@app.post("/api/chat")
async def chat(request: Request):

    try:

        data = await request.json()

        message = data.get("message", "")

        if not message:
            return JSONResponse(
                status_code=400,
                content={
                    "reply": "Empty message."
                }
            )

        # =============================================
        # SIMPLE JARVIS RESPONSES
        # =============================================

        msg = message.lower()

        if "hello" in msg or "hi" in msg:
            reply = "Hello Mr. Aryan. Jarvis systems are online."

        elif "how are you" in msg:
            reply = "I am functioning perfectly Mr. Aryan."

        elif "your name" in msg:
            reply = "I am Jarvis, your advanced AI assistant."

        elif "time" in msg:
            from datetime import datetime
            reply = f"The current time is {datetime.now().strftime('%I:%M %p')}"

        elif "date" in msg:
            from datetime import datetime
            reply = f"Today's date is {datetime.now().strftime('%d %B %Y')}"

        else:
            reply = f"You said: {message}"

        return {
            "reply": reply
        }

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "reply": f"Server Error: {str(e)}"
            }
        )

# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }
