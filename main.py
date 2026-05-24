import asyncio
import os
import sys
import platform
import webbrowser
import subprocess
from datetime import datetime

# Windows-only keyboard module
if platform.system() == "Windows":
    import msvcrt
else:
    msvcrt = None

from voice_engine import VoiceEngine
from brain import Brain
from config import USER_NAME, ASSISTANT_NAME, OPENROUTER_API_KEY


# ─────────────────────────────────────────────────────────────
# Instant Command Handler
# ─────────────────────────────────────────────────────────────

def execute_command(query: str):
    """
    Fast command handler.
    Executes simple commands instantly without AI processing.
    """

    q = query.lower().strip()

    # ── Browser & Websites ──

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

    # ── Stop Speech ──

    if q in {
        "stop",
        "stop jarvis",
        "quiet",
        "shut up",
        "silence",
        "enough"
    }:
        return "__STOP__"

    # ── Windows-only System Apps ──

    if platform.system() == "Windows":

        if "open notepad" in q:
            subprocess.Popen("notepad.exe")
            return "Opening Notepad."

        if "open calculator" in q:
            subprocess.Popen("calc.exe")
            return "Opening Calculator."

        if "open file explorer" in q or "open explorer" in q:
            subprocess.Popen("explorer.exe")
            return "Opening File Explorer."

        if "open task manager" in q:
            subprocess.Popen("taskmgr.exe")
            return "Opening Task Manager."

        if "open settings" in q:
            subprocess.Popen("ms-settings:", shell=True)
            return "Opening Windows Settings."

        if "shutdown" in q or "shut down" in q:
            subprocess.Popen("shutdown /s /t 10")
            return "Shutting down in 10 seconds Mr. Aryan."

        if "cancel shutdown" in q:
            subprocess.Popen("shutdown /a")
            return "Shutdown cancelled."

        if "restart" in q:
            subprocess.Popen("shutdown /r /t 10")
            return "Restarting in 10 seconds Mr. Aryan."

    # ── VS Code ──

    if "open vs code" in q or "open visual studio code" in q:

        try:
            subprocess.Popen(["code", "."])
            return "Opening VS Code."

        except Exception:
            return "VS Code is not installed Mr. Aryan."

    # ── Output Folder ──

    if (
        "open output" in q or
        "open jarvis output" in q or
        "show my files" in q
    ):

        output_dir = os.path.join(
            os.path.expanduser("~"),
            "JarvisOutput"
        )

        os.makedirs(output_dir, exist_ok=True)

        if platform.system() == "Windows":
            subprocess.Popen(f'explorer "{output_dir}"')

        return "Opening your Jarvis output folder."

    return None


# ─────────────────────────────────────────────────────────────
# Keyboard Stop Listener
# ─────────────────────────────────────────────────────────────

async def check_for_stop(voice: VoiceEngine):
    """
    Press S / Space / Enter / ESC to stop speech.
    Disabled automatically on Linux/Render.
    """

    if msvcrt is None:
        return

    while True:

        try:

            if msvcrt.kbhit():

                key = msvcrt.getch()

                if key in [
                    b's',
                    b'S',
                    b' ',
                    b'\x1b',
                    b'\r'
                ]:
                    voice.stop()

        except Exception:
            pass

        await asyncio.sleep(0.05)


# ─────────────────────────────────────────────────────────────
# Typewriter Print
# ─────────────────────────────────────────────────────────────

async def slow_print(
    text: str,
    delay: float = 0.01
):
    """
    Prints text with a typewriter effect.
    """

    sys.stdout.write("JARVIS: ")

    for char in text:

        sys.stdout.write(char)
        sys.stdout.flush()

        await asyncio.sleep(delay)

    print()


# ─────────────────────────────────────────────────────────────
# Main Loop
# ─────────────────────────────────────────────────────────────

async def main():

    if (
        not OPENROUTER_API_KEY or
        "your_key_here" in OPENROUTER_API_KEY
    ):

        print(
            "Error: OpenRouter API Key "
            "not found in .env file."
        )

        return

    voice = VoiceEngine()

    brain = Brain(voice)

    asyncio.create_task(
        check_for_stop(voice)
    )

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
        f"{greeting} Mr. Aryan. "
        f"Systems are fully online and "
        f"all cores are operational. "
        f"How can I assist you today?"
    )

    print(f"JARVIS: {startup_msg}")

    print(
        "\n[TIP] Say 'stop jarvis' "
        "to instantly stop speaking."
    )

    print(
        "[TIP] Press 'S' key to stop "
        "(Windows only)."
    )

    print(
        "[TIP] Say 'go to sleep' "
        "to pause Jarvis.\n"
    )

    try:
        await voice.speak(startup_msg)
    except Exception:
        pass

    state = "SLEEPING"

    while True:

        try:

            query = await asyncio.to_thread(
                voice.listen
            )

            if not query:
                continue

            # ── Sleep Commands ──

            if any(
                cmd in query
                for cmd in [
                    "go to sleep",
                    "goodbye",
                    "bye jarvis"
                ]
            ):

                if state == "ACTIVE":

                    print(f"You: {query}")

                    resp = (
                        "Of course Mr. Aryan. "
                        "Entering standby mode."
                    )

                    await slow_print(resp)

                    try:
                        await voice.speak(resp)
                    except Exception:
                        pass

                state = "SLEEPING"

                continue

            # ── Wake Word ──

            if (
                ASSISTANT_NAME.lower() in query or
                "hey jarvis" in query
            ):

                if state == "SLEEPING":
                    state = "ACTIVE"

                print(f"You: {query}")

                clean_q = (
                    query.replace(
                        ASSISTANT_NAME.lower(),
                        ""
                    )
                    .replace("hey jarvis", "")
                    .strip()
                )

                if not clean_q:

                    resp = (
                        "Yes Mr. Aryan, "
                        "how can I help you?"
                    )

                    await slow_print(resp)

                    try:
                        await voice.speak(resp)
                    except Exception:
                        pass

                    continue

                query = clean_q

            elif state == "SLEEPING":
                continue

            # ── Active State ──

            if state == "ACTIVE":

                cmd_resp = execute_command(query)

                if cmd_resp:

                    if cmd_resp == "__STOP__":

                        voice.stop()

                        print("[Jarvis] Stopped.")

                        continue

                    print(f"You: {query}")

                    await slow_print(cmd_resp)

                    try:
                        await voice.speak(cmd_resp)
                    except Exception:
                        pass

                    continue

                print(f"You: {query}")

                response_text = await brain.think(query)

                if response_text:

                    await slow_print(response_text)

                    try:
                        await voice.speak(response_text)
                    except Exception:
                        pass

        except KeyboardInterrupt:

            print(
                "\n[Jarvis] Shutting down. "
                "Goodbye Mr. Aryan."
            )

            break

        except Exception as e:

            print(f"\n[System Error]: {e}")

            await asyncio.sleep(0.1)


# ─────────────────────────────────────────────────────────────
# Start
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        pass
