import asyncio
import os
import re
import threading
import time
from uuid import uuid4

import edge_tts
import pygame
from langdetect import detect

# Initialize pygame mixer
if not pygame.mixer.get_init():
    pygame.mixer.init(
        frequency=22050,
        size=-16,
        channels=1,
        buffer=512
    )

# Hinglish/Hindi detection words
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
    """Detect Hindi or Hinglish."""

    # Detect Hindi script
    if any('\u0900' <= ch <= '\u097f' for ch in text):
        return True

    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

    if not words:
        return False

    matches = sum(1 for w in words if w in HINGLISH_WORDS)

    return matches >= 2 or (matches / len(words)) >= 0.2


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
    # TEXT CLEANING
    # ---------------------------------------------------------

    def clean_text(self, text):
        """Clean text for natural speech."""

        # Remove think tags
        text = re.sub(
            r'<think>.*?</think>',
            '',
            text,
            flags=re.DOTALL
        )

        # Remove markdown/symbols
        text = re.sub(r'[*_#`~]', '', text)

        # Fix spaced letters:
        # H e l l o -> Hello
        text = re.sub(
            r'(?:\b[a-zA-Z]\b(?:\s+|$)){2,}',
            lambda m: ''.join(m.group(0).split()),
            text
        )

        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()

        # Better pronunciation replacements
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
    # SENTENCE SPLITTING
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
    # AUDIO PLAYBACK
    # ---------------------------------------------------------

    def play_audio(self, filename):

        self.is_speaking = True

        try:

            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():

                if self.stop_event.is_set():
                    pygame.mixer.music.stop()
                    break

                time.sleep(0.05)

        except Exception as e:
            print(f"[Audio Error]: {e}")

        finally:

            try:
                pygame.mixer.music.unload()
            except:
                pass

            time.sleep(0.1)

            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except:
                    pass

            self.is_speaking = False

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

            # More natural speaking rate
            speech_rate = "+18%" if lang == "hi" else "+5%"

            communicate = edge_tts.Communicate(
                sentence,
                voice,
                rate=speech_rate,
                pitch="+0Hz"
            )

            await communicate.save(filename)

            await asyncio.to_thread(
                self.play_audio,
                filename
            )

        except Exception as e:

            print(f"[TTS Error]: {e}")

            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except:
                    pass

    # ---------------------------------------------------------
    # VOICE STOP CALLBACK
    # ---------------------------------------------------------

    def _on_stop_phrase_heard(self, recognizer, audio):

        try:

            text = recognizer.recognize_google(audio)

            text = text.lower().strip()

            if any(p in text for p in self.STOP_PHRASES):

                print("\n[Jarvis] Stop command detected.")

                self.stop()

        except:
            pass

    # ---------------------------------------------------------
    # START BACKGROUND STOP LISTENER
    # ---------------------------------------------------------

    def _start_voice_stopper(self):

        if self._bg_stopper is not None:
            return

        try:

            import speech_recognition as sr

            recognizer = sr.Recognizer()

            recognizer.dynamic_energy_threshold = True

            mic = sr.Microphone()

            self._bg_stopper = recognizer.listen_in_background(
                mic,
                self._on_stop_phrase_heard,
                phrase_time_limit=2
            )

        except Exception as e:

            print(f"[Voice Stopper Error]: {e}")

            self._bg_stopper = None

    # ---------------------------------------------------------
    # STOP BACKGROUND LISTENER
    # ---------------------------------------------------------

    def _stop_voice_stopper(self):

        if self._bg_stopper:

            try:
                self._bg_stopper(wait_for_stop=False)
            except:
                pass

            self._bg_stopper = None

    # ---------------------------------------------------------
    # MAIN SPEAK FUNCTION
    # ---------------------------------------------------------

    async def speak(self, text):

        text = self.clean_text(text)

        if not text:
            return

        self.stop_event.clear()

        sentences = self.split_sentences(text)

        self._start_voice_stopper()

        try:

            for sentence in sentences:

                if self.stop_event.is_set():
                    break

                await self._speak_sentence(sentence)

        finally:

            self._stop_voice_stopper()

    # ---------------------------------------------------------
    # STOP SPEECH
    # ---------------------------------------------------------

    def stop(self):

        self.stop_event.set()

        try:
            pygame.mixer.music.stop()
        except:
            pass

    # ---------------------------------------------------------
    # MICROPHONE LISTEN
    # ---------------------------------------------------------

    def listen(self):

        import speech_recognition as sr

        recognizer = sr.Recognizer()

        try:

            mic = sr.Microphone()

            with mic as source:

                recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.5
                )

                try:

                    audio = recognizer.listen(
                        source,
                        timeout=10,
                        phrase_time_limit=10
                    )

                    query = recognizer.recognize_google(audio)

                    return query.strip()

                except:
                    return ""

        except Exception as e:

            print(f"\n[Mic Error]: {e}")

            time.sleep(1)

            return ""


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    async def test():

        engine = VoiceEngine()

        await engine.speak(
            "Hello Aryan. "
            "Your Jarvis voice engine is now fully upgraded. "
            "I can now speak naturally without spelling words. "
            "Artificial Intelligence and G P T pronunciation "
            "will also sound much better now."
        )

    asyncio.run(test())
