from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from brain import Brain
from voice_engine import VoiceEngine

import os

# =====================================================
# CREATE STATIC FOLDER
# =====================================================

os.makedirs("static", exist_ok=True)

# =====================================================
# APP
# =====================================================

app = FastAPI(title="JARVIS")

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
# STATIC FILES
# =====================================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

# =====================================================
# INIT
# =====================================================

brain = Brain()
voice = VoiceEngine()

# =====================================================
# ROUTES
# =====================================================

@app.get("/")
async def home():

    return {
        "status": "Jarvis Online"
    }


@app.post("/chat")
async def chat(request: Request):

    try:

        data = await request.json()

        user_text = data.get("text", "")

        if not user_text:

            return {
                "response": "Please say something.",
                "audio": None
            }

        # AI response
        response_text = await brain.think(user_text)

        # Generate TTS
        audio_file = await voice.generate_voice(
            response_text
        )

        return {
            "response": response_text,
            "audio": audio_file
        }

    except Exception as e:

        return {
            "response": f"Server Error: {str(e)}",
            "audio": None
        }
