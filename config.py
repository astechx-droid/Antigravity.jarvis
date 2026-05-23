import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1"
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# Piper Local TTS Configuration (High-Stability & Fluent)
PIPER_EXE = os.path.join(os.getcwd(), "piper", "piper.exe")
PIPER_VOICES = {
    "en": os.path.join(os.getcwd(), "piper", "en_US-ryan-high.onnx"),
    "hi": os.path.join(os.getcwd(), "piper", "hi_IN-rohan-medium.onnx")
}
PIPER_SPEED = 0.85 # Slightly faster for natural human cadence (0.85-0.9 is best)

# Assistant Identity
USER_NAME = "Mr. Aryan"
ASSISTANT_NAME = "JARVIS"

# Speech Settings
DEFAULT_LANGUAGE = "en"

# Database path
DB_PATH = "jarvis_memory.db"
