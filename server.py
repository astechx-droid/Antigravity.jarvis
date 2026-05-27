from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import edge_tts
import os
from uuid import uuid4

app = FastAPI()

# -------------------------------
# CORS
# -------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# STATIC SETUP
# -------------------------------

if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------------
# ROOT
# -------------------------------

@app.get("/")
async def root():
    return {"status": "Jarvis server online"}

# -------------------------------
# TTS API
# -------------------------------

@app.post("/api/tts")
async def tts(request: Request):
    try:
        data = await request.json()

        text = data.get("text", "").strip()

        if not text:
            return JSONResponse(
                status_code=400,
                content={"error": "No text provided"}
            )

        # Hindi / English Voice
        hindi_words = [
            "hai", "kya", "kaise", "mera",
            "bhai", "yaar", "tum", "main"
        ]

        lower = text.lower()

        if any(word in lower for word in hindi_words):
            voice = "hi-IN-MadhurNeural"
        else:
            voice = "en-IN-PrabhatNeural"

        filename = f"{uuid4()}.mp3"
        filepath = os.path.join("static", filename)

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate="+10%"
        )

        await communicate.save(filepath)

        return {
            "audio_url": f"/static/{filename}"
        }

    except Exception as e:
        print("[TTS ERROR]", e)

        return JSONResponse(
            status_code=500,
            content={
                "error": str(e)
            }
        )
