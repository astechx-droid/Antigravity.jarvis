import asyncio
import os
import re
import threading
import time
from uuid import uuid4
import edge_tts
import pygame
from langdetect import detect

# Initialize Pygame Mixer for audio playback
if not pygame.mixer.get_init():
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

# Common Hinglish/Hindi words in English letters to detect conversational Hinglish
HINGLISH_WORDS = {
    "main", "hoon", "he", "hu", "aap", "bataiye", "batao", "kaise", "hain", "hai", "ho", "duniya", "mein", "me",
    "bahut", "kuch", "chal", "raha", "rahi", "kya", "karun", "kar", "se", "ki", "ko", "ka", "aur", "toh", "to", "na",
    "nahin", "nahi", "theek", "thik", "achha", "achhi", "acha", "haan", "han", "karo", "karta", "karti", "rahe",
    "yaar", "kuchh", "kya", "kyu", "kyun", "kab", "kaha", "kahan", "kaise", "kaun", "hai", "meri", "mera", "mere",
    "tum", "tumhara", "tumhari", "aapka", "aapki", "aapke", "liye", "bhai", "sab", "theek", "hoga", "hogi", "hoge"
}

def is_hindi_or_hinglish(text):
    # Check for Devanagari range
    if any(u'\u0900' <= char <= u'\u097f' for char in text):
        return True
    
    # Check for common Hinglish words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    if not words:
        return False
    
    match_count = sum(1 for w in words if w in HINGLISH_WORDS)
    # If at least 2 words or 20% of words are Hinglish, classify as Hindi/Hinglish
    return match_count >= 2 or (match_count / len(words)) >= 0.2

class VoiceEngine:
    # Keywords that trigger an instant voice-stop
    STOP_PHRASES = {"stop", "stop jarvis", "quiet", "shut up", "silence", "enough", "bas", "ruko"}

    def __init__(self):
        self.is_speaking = False
        self.stop_event = threading.Event()
        self._bg_stopper = None   # holds the stop-function from listen_in_background

    def get_voice(self, text):
        """Detect language and return the corresponding neural voice."""
        if is_hindi_or_hinglish(text):
            return "hi-IN-MadhurNeural", "hi"
        try:
            lang = detect(text)
            voices = {
                'hi': "hi-IN-MadhurNeural",
                'en': "en-GB-RyanNeural",
                'es': "es-ES-AlvaroNeural",
                'fr': "fr-FR-HenriNeural"
            }
            return voices.get(lang, "en-GB-RyanNeural"), lang
        except:
            return "en-GB-RyanNeural", "en"

    def clean_text(self, text):
        """Remove markdown, think tags, and special symbols."""
        t = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        t = re.sub(r'\*+', '', t)
        t = re.sub(r'#+', '', t)
        t = re.sub(r'`+', '', t)
        return t.strip()

    def split_sentences(self, text):
        """
        Split text into natural speaking sentences.
        Handles abbreviations (Mr., Dr., Mrs., etc.) so they
        are never treated as sentence boundaries.
        """
        # Common abbreviations that should NOT trigger a sentence split
        abbreviations = r'(?:Mr|Mrs|Ms|Dr|Jr|Sr|Prof|St|vs|etc|approx|dept|govt|inc|ltd)'
        # Replace abbreviation periods with a placeholder
        protected = re.sub(rf'\b({abbreviations})\.\s', r'\1<DOT> ', text)
        # Split on real sentence endings: . ! ? followed by whitespace
        parts = re.split(r'(?<=[.!?])\s+', protected.strip())
        # Restore placeholders
        result = []
        for p in parts:
            restored = p.replace('<DOT>', '.').strip()
            if restored:
                result.append(restored)
        return result

    def play_audio(self, filename):
        """Play a single mp3 file synchronously."""
        self.is_speaking = True
        try:
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            # Use time.sleep instead of Clock().tick — more reliable
            while pygame.mixer.music.get_busy():
                if self.stop_event.is_set():
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.05)
        except Exception as e:
            pass
        finally:
            try:
                pygame.mixer.music.unload()
            except:
                pass
            # Small pause to release the file handle before deleting
            time.sleep(0.1)
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except:
                    pass
            self.is_speaking = False

    async def _speak_sentence(self, sentence):
        """Generate TTS audio for one sentence and play it."""
        if self.stop_event.is_set():
            return
        voice, lang = self.get_voice(sentence)
        filename = os.path.join(os.getcwd(), f"speech_{uuid4()}.mp3")
        try:
            # 1.5x (+50%) speed for Hindi, +5% for others as natural
            speech_rate = "+50%" if lang == "hi" else "+5%"
            communicate = edge_tts.Communicate(sentence, voice, rate=speech_rate)
            await communicate.save(filename)
            # Run blocking playback in a thread so it doesn't block the event loop
            await asyncio.to_thread(self.play_audio, filename)
        except Exception as e:
            # Clean up on any error so no orphan files are left
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except:
                    pass

    # ── Voice-Triggered Stop ──────────────────────────────────

    def _on_stop_phrase_heard(self, recognizer, audio):
        """
        Background callback: runs in a daemon thread while Jarvis is speaking.
        If a stop phrase is detected, kills playback immediately.
        """
        try:
            text = recognizer.recognize_google(audio).lower().strip()
            if any(phrase in text for phrase in self.STOP_PHRASES):
                print("\n[Jarvis] Voice stop detected — stopping speech.")
                self.stop()
        except:
            pass  # Ignore unrecognised audio silently

    def _start_voice_stopper(self):
        """Start a background mic listener ONLY while speaking."""
        if self._bg_stopper is not None:
            return  # Already active
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            # Let the recognizer dynamically adjust to noise/mic volume instead of hardcoding
            r.dynamic_energy_threshold = True
            m = sr.Microphone()
            # listen_in_background returns a stop-function
            self._bg_stopper = r.listen_in_background(
                m, self._on_stop_phrase_heard, phrase_time_limit=2
            )
        except Exception as e:
            self._bg_stopper = None

    def _stop_voice_stopper(self):
        """Stop the background mic listener."""
        if self._bg_stopper:
            try:
                self._bg_stopper(wait_for_stop=False)
            except:
                pass
            self._bg_stopper = None

    # ── Main Speak ───────────────────────────────────────────

    async def speak(self, text):
        """
        Speak full text by splitting into sentences.
        Activates a background voice-stopper so saying 'stop jarvis'
        kills playback instantly mid-sentence.
        """
        text = self.clean_text(text)
        if not text:
            return

        self.stop_event.clear()
        sentences = self.split_sentences(text)

        # Start background listener before first sentence
        self._start_voice_stopper()
        try:
            for sentence in sentences:
                if self.stop_event.is_set():
                    break
                await self._speak_sentence(sentence)
        finally:
            # Always stop listener after speech finishes or is interrupted
            self._stop_voice_stopper()

    def stop(self):
        """Interrupt current speech immediately (keyboard 'S' or voice 'stop jarvis')."""
        self.stop_event.set()
        try:
            pygame.mixer.music.stop()
        except:
            pass

    def listen(self):
        """Listen via microphone and return recognized speech."""
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        try:
            mic = sr.Microphone()
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                try:
                    audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
                    query = recognizer.recognize_google(audio)
                    return query.lower()
                except:
                    return ""
        except Exception as e:
            print(f"\n[Mic Error]: Could not access microphone. {e}")
            time.sleep(1) # Sleep to avoid spamming the console
            return ""

if __name__ == "__main__":
    async def test():
        engine = VoiceEngine()
        await engine.speak(
            "Hello Mr. Aryan. The voice engine has been upgraded. "
            "I now speak every sentence clearly without stopping. "
            "Each sentence is processed individually for maximum reliability."
        )
    asyncio.run(test())
