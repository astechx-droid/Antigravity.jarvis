import os
from uuid import uuid4

import edge_tts


class VoiceEngine:

    def __init__(self):

        # Static folder create
        os.makedirs("static", exist_ok=True)

    async def generate_voice(self, text):

        if not text:
            return None

        # Better pronunciation fixes
        replacements = {
            "AI": "Artificial Intelligence",
            "GPT": "G P T",
            "API": "A P I",
            "HTML": "H T M L",
            "CSS": "C S S",
            "JS": "Java Script",
            "SQL": "S Q L",
            "OpenAI": "Open A I",
            "ChatGPT": "Chat G P T"
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Hinglish detection
        hindi_words = [
            "hai", "kya", "kaise", "mera", "meri",
            "bhai", "yaar", "acha", "kar", "nahi"
        ]

        is_hindi = any(word in text.lower() for word in hindi_words)

        # Voice selection
        if is_hindi:
            voice = "hi-IN-MadhurNeural"
            rate = "+12%"
        else:
            voice = "en-IN-PrabhatNeural"
            rate = "+5%"

        filename = f"{uuid4()}.mp3"

        filepath = os.path.join(
            "static",
            filename
        )

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch="+0Hz"
        )

        await communicate.save(filepath)

        return f"/static/{filename}"
