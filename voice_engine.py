import asyncio
import os
import re
import threading
import time
from uuid import uuid4

import edge_tts
from langdetect import detect

# ---------------------------------------------------------
# HINGLISH DETECTION
# ---------------------------------------------------------

HINGLISH_WORDS = {
    "main", "hoon", "hu", "hai", "hain", "ho",
    "aap", "tum", "mera", "meri", "mere",
    "ka", "ki", "ke", "ko", "se", "mein", "me",
    "kya", "kyu", "kyun", "kaise", "kab",
    "kahan", "yaar", "bhai", "acha", "achha",
    "theek", "thik", "haan", "han", "nahi",
    "nahin", "kar", "karo", "karna", "karun",
    "chal", "raha", "rahi", "liye", "toh",
    "to", "na", "sab", "bahut", "kuch"
}


def is_hindi_or_hinglish(text):
    if any('\u0900' <= ch <= '\u097f' for ch in text):
        return True

    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

    if not words:
        return False

    matches = sum(1 for w in words if w in HINGLISH_WORDS)

    return matches >= 2 or (matches / len(words)) >= 0.2


# ---------------------------------------------------------
# VOICE ENGINE
# ---------------------------------------------------------

class VoiceEngine:

    STOP_PHRASES = {
        "stop",
        "stop jarvis",
        "quiet",
        "shut up",
        "silence",
        "enough",
        "bas",
        "ruko"
    }

    def __init__(self):

        self.is_speaking = False
        self.stop_event = threading.Event()
        self._bg_stopper = None

        # Render/Linux detection
        self.is_render = os.environ.get("RENDER") is not None

    # ---------------------------------------------------------
    # VOICE SELECTION
    # ---------------------------------------------------------

    def get_voice(self, text):

        if is_hindi_or_hinglish(text):
            return "hi-IN-SwaraNeural", "hi"

        try:

            lang = detect(text)

            voices = {
                "hi": "hi-IN-SwaraNeural",
                "en": "en-IN-PrabhatNeural",
                "es": "es-ES-AlvaroNeural",
                "fr": "fr-FR-HenriNeural"
            }

            return voices.get(lang, "en-IN-PrabhatNeural"), lang

        except:
            return "en-IN-PrabhatNeural", "en"

    # ---------------------------------------------------------
    # CLEAN TEXT
    # ---------------------------------------------------------

    def clean_text(self, text):

        text = re.sub(
            r'<think>.*?</think>',
            '',
            text,
            flags=re.DOTALL
        )

        text = re.sub(r'[*_#`~]', '', text)

        text = re.sub(
            r'(?:\b[a-zA-Z]\b(?:\s+|$)){2,}',
            lambda m: ''.join(m.group(0).split()),
            text
        )

        text = re.sub(r'\s+', ' ', text).strip()

        replacements = {
            "AI": "Artificial Intelligence",
            "A.I.": "Artificial Intelligence",
            "GPT": "G P T",
            "API": "A P I",
            "HTML": "H T M L",
            "CSS": "C S S",
            "JS": "Java Script",
            "SQL": "S Q L",
            "JarvisAI": "Jarvis AI"
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    # ---------------------------------------------------------
    # SPLIT SENTENCES
    # ---------------------------------------------------------

    def split_sentences(self, text):

        abbreviations = (
            r'(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|approx|dept|govt|inc|ltd)'
        )

        protected = re.sub(
            rf'\b({abbreviations})\.\s',
            r'\1<DOT> ',
            text
        )

        parts = re.split(
            r'(?<=[.!?])\s+',
            protected.strip()
        )

        result = []

        for part in parts:

            restored = part.replace('<DOT>', '.').strip()

            if restored:
                result.append(restored)

        return result

    # ---------------------------------------------------------
    # SPEAK SENTENCE
    # ---------------------------------------------------------

    async def _speak_sentence(self, sentence):

        if self.stop_event.is_set():
            return

        voice, lang = self.get_voice(sentence)

        filename = os.path.join(
            os.getcwd(),
            f"speech_{uuid4()}.mp3"
        )

        try:

            speech_rate = "+18%" if lang == "hi" else "+5%"

            communicate = edge_tts.Communicate(
                sentence,
                voice,
                rate=speech_rate,
                pitch="+0Hz"
            )

            await communicate.save(filename)

            # Render pe audio play mat karo
            if self.is_render:
                print(f"[Render TTS]: {sentence}")

                if os.path.exists(filename):
                    os.remove(filename)

                return

            # Local PC pe hi play karo
            from playsound import playsound

            self.is_speaking = True

            await asyncio.to_thread(
                playsound,
                filename
            )

        except Exception as e:

            print(f"[TTS Error]: {e}")

        finally:

            self.is_speaking = False

            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except:
                    pass

    # ---------------------------------------------------------
    # MAIN SPEAK
    # ---------------------------------------------------------

    async def speak(self, text):

        text = self.clean_text(text)

        if not text:
            return

        self.stop_event.clear()

        sentences = self.split_sentences(text)

        for sentence in sentences:

            if self.stop_event.is_set():
                break

            await self._speak_sentence(sentence)

    # ---------------------------------------------------------
    # STOP
    # ---------------------------------------------------------

    def stop(self):

        self.stop_event.set()

    # ---------------------------------------------------------
    # LISTEN
    # ---------------------------------------------------------

    def listen(self):

        # Render pe microphone disabled
        if self.is_render:
            return ""

        import speech_recognition as sr

        recognizer = sr.Recognizer()

        try:

            mic = sr.Microphone()

            with mic as source:

                recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.5
                )

                audio = recognizer.listen(
                    source,
                    timeout=10,
                    phrase_time_limit=10
                )

                query = recognizer.recognize_google(audio)

                return query.strip()

        except:
            return ""


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    async def test():

        engine = VoiceEngine()

        await engine.speak(
            "Hello Aryan. Your Jarvis voice engine is now fixed."
        )

    asyncio.run(test())
