import asyncio
import os
import sys
import msvcrt
import webbrowser
import subprocess
from datetime import datetime
from voice_engine import VoiceEngine
from brain import Brain
from config import USER_NAME, ASSISTANT_NAME, OPENROUTER_API_KEY

# ─── Instant Command Handler ──────────────────────────────────

def execute_command(query: str):
    """Fast command handler — executes instantly without AI processing."""
    q = query.lower().strip()

    # Browser & Websites
    if "open chrome" in q:
        webbrowser.open("https://www.google.com")
        return "Opening Chrome."
    if "open youtube" in q:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."
    if "open google" in q:
        webbrowser.open("https://www.google.com")
        return "Opening Google."
    if "open github" in q:
        webbrowser.open("https://www.github.com")
        return "Opening GitHub."
    if "open chatgpt" in q:
        webbrowser.open("https://chat.openai.com")
        return "Opening ChatGPT."

    # Voice Stop (handled here when Jarvis is NOT speaking)
    if q in {"stop", "stop jarvis", "quiet", "shut up", "silence", "enough"}:
        return "__STOP__"  # Special signal handled in main loop

    # System Apps
    if "open notepad" in q:
        subprocess.Popen("notepad.exe")
        return "Opening Notepad."
    if "open calculator" in q:
        subprocess.Popen("calc.exe")
        return "Opening Calculator."
    if "open file explorer" in q or "open explorer" in q:
        subprocess.Popen("explorer.exe")
        return "Opening File Explorer."
    if "open vs code" in q or "open visual studio code" in q:
        try:
            subprocess.Popen(["code", "."])
            return "Opening VS Code."
        except FileNotFoundError:
            return "VS Code is not installed Mr. Aryan."
    if "open task manager" in q:
        subprocess.Popen("taskmgr.exe")
        return "Opening Task Manager."
    if "open settings" in q:
        subprocess.Popen("ms-settings:", shell=True)
        return "Opening Windows Settings."

    # Output Folder
    if "open output" in q or "open jarvis output" in q or "show my files" in q:
        output_dir = os.path.join(os.path.expanduser("~"), "JarvisOutput")
        os.makedirs(output_dir, exist_ok=True)
        subprocess.Popen(f'explorer "{output_dir}"')
        return "Opening your Jarvis output folder."

    # System Controls
    if "shutdown" in q or "shut down" in q:
        subprocess.Popen("shutdown /s /t 10")
        return "Shutting down in 10 seconds Mr. Aryan."
    if "cancel shutdown" in q:
        subprocess.Popen("shutdown /a")
        return "Shutdown cancelled."
    if "restart" in q:
        subprocess.Popen("shutdown /r /t 10")
        return "Restarting in 10 seconds Mr. Aryan."

    return None


# ─── Background Key Watcher ───────────────────────────────────

async def check_for_stop(voice: VoiceEngine):
    """Press S, Space, Enter, or Escape to stop Jarvis speaking."""
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            try:
                # Stop speaking on S, Space, Escape, or Enter keypress
                if key in [b's', b'S', b' ', b'\x1b', b'\r']:
                    voice.stop()
            except:
                pass
        await asyncio.sleep(0.05)


# ─── Typing Print ─────────────────────────────────────────────

async def slow_print(text: str, delay: float = 0.01):
    """Prints text with a typewriter effect."""
    sys.stdout.write("JARVIS: ")
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        await asyncio.sleep(delay)
    print()


# ─── Main Loop ────────────────────────────────────────────────

async def main():
    if not OPENROUTER_API_KEY or "your_key_here" in OPENROUTER_API_KEY:
        print("Error: OpenRouter API Key not found in .env file.")
        return

    voice = VoiceEngine()
    brain = Brain(voice)
    asyncio.create_task(check_for_stop(voice))

    # ── Greeting ──
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 17:
        greeting = "Good afternoon"
    elif 17 <= hour < 21:
        greeting = "Good evening"
    else:
        greeting = "Good night"

    startup_msg = (
        f"{greeting} Mr. Aryan. Systems are fully online and all cores are operational. "
        f"How can I assist you today?"
    )
    print(f"JARVIS: {startup_msg}")
    print(f"\n  [TIP] Say 'stop jarvis' anytime to instantly stop speaking.")
    print(f"  [TIP] Press 'S' key to stop. Say 'go to sleep' to pause.")
    print(f"  [TIP] Say 'hey jarvis' or 'jarvis' to wake up.\n")
    await voice.speak(startup_msg)

    state = "SLEEPING"

    while True:
        try:
            query = await asyncio.to_thread(voice.listen)

            if not query:
                continue

            # ── Wake / Sleep control ──
            if any(cmd in query for cmd in ["go to sleep", "goodbye", "bye jarvis"]):
                if state == "ACTIVE":
                    print(f"You: {query}")
                    resp = f"Of course Mr. Aryan. Entering standby mode."
                    await slow_print(resp)
                    await voice.speak(resp)
                state = "SLEEPING"
                continue

            # ── Wake word ──
            if ASSISTANT_NAME.lower() in query or "hey jarvis" in query:
                if state == "SLEEPING":
                    state = "ACTIVE"
                print(f"You: {query}")
                clean_q = (
                    query.replace(ASSISTANT_NAME.lower(), "")
                    .replace("hey jarvis", "")
                    .strip()
                )
                if not clean_q:
                    resp = f"Yes Mr. Aryan, how can I help you?"
                    await slow_print(resp)
                    await voice.speak(resp)
                    continue
                query = clean_q

            elif state == "SLEEPING":
                continue

            # ── Active state: process query ──
            if state == "ACTIVE":
                # Fast command handler first
                cmd_resp = execute_command(query)
                if cmd_resp:
                    # __STOP__ is a silent stop signal — no speech needed
                    if cmd_resp == "__STOP__":
                        voice.stop()
                        print("[Jarvis] Stopped.")
                        continue
                    print(f"You: {query}")
                    await slow_print(cmd_resp)
                    await voice.speak(cmd_resp)
                    continue

                print(f"You: {query}")

                # AI Brain — handles chat, tools, and heavy tasks
                response_text = await brain.think(query)

                if response_text:
                    await slow_print(response_text)
                    await voice.speak(response_text)

        except KeyboardInterrupt:
            print("\n[Jarvis] Shutting down. Goodbye Mr. Aryan.")
            break
        except Exception as e:
            print(f"\n[System Error]: {e}")
            await asyncio.sleep(0.1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
