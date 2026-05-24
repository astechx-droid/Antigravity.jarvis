import asyncio
import edge_tts
import pygame
import os
import time

async def test_voice():
    print("--- Edge TTS Test ---")
    voice = "en-US-ChristopherNeural"
    text = "Hello Mr Aryan, this is a test of the Edge T T S voice engine. Can you hear me?"
    temp_file = "test_voice.mp3"
    
    try:
        print(f"Synthesizing to {temp_file}...")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(temp_file)
        
        if os.path.exists(temp_file):
            print("File created. Initializing pygame...")
            pygame.mixer.init()
            print("Loading and playing...")
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            print("Playback finished. Cleaning up...")
            pygame.mixer.music.unload()
            os.remove(temp_file)
            print("All good!")
        else:
            print("Error: File was not created.")
            
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_voice())
