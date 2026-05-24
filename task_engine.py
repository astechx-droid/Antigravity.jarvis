"""
task_engine.py — Handles heavy tasks for Jarvis:
- Code generation (writes files + opens in VS Code)
- Script execution (runs Python scripts, reports output)
- Document writing (saves .txt / .md files)
"""

import os
import re
import subprocess
import sys
import openai
from datetime import datetime
from config import OPENROUTER_API_KEY, OPENROUTER_URL

# Output folder — all generated files go here
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "JarvisOutput")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Model for heavy/coding tasks — smarter, longer context
TASK_MODEL = "google/gemini-2.0-flash-exp:free"

# ─── Keyword Detection ────────────────────────────────────────

CODE_KEYWORDS = [
    "write a", "write me a", "create a", "make a", "build a",
    "code", "script", "program", "function", "class", "algorithm",
    "write code", "generate code", "write python", "write html",
    "write js", "write javascript", "write css",
]

RUN_KEYWORDS = [
    "run", "execute", "test this", "run this script", "run the script"
]

DOC_KEYWORDS = [
    "write a report", "write an essay", "write a document",
    "write notes", "write a summary", "write a plan", "write a letter"
]


def is_heavy_task(query: str) -> bool:
    """Returns True if query is a heavy task (code, run, document)."""
    q = query.lower()
    return (
        any(kw in q for kw in CODE_KEYWORDS) or
        any(kw in q for kw in RUN_KEYWORDS) or
        any(kw in q for kw in DOC_KEYWORDS)
    )


def detect_task_type(query: str) -> str:
    """Detect which kind of heavy task this is."""
    q = query.lower()
    if any(kw in q for kw in RUN_KEYWORDS):
        return "run"
    if any(kw in q for kw in DOC_KEYWORDS):
        return "document"
    return "code"


# ─── AI Client (task-grade model) ─────────────────────────────

def get_client():
    return openai.OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_URL)


# ─── Code Generation ──────────────────────────────────────────

def detect_language(query: str) -> tuple[str, str]:
    """Returns (language_name, file_extension) based on the query."""
    q = query.lower()
    if "html" in q:
        return "HTML", "html"
    if "css" in q:
        return "CSS", "css"
    if "javascript" in q or " js " in q:
        return "JavaScript", "js"
    if "java " in q:
        return "Java", "java"
    if "c++" in q or "cpp" in q:
        return "C++", "cpp"
    if "bash" in q or "shell" in q:
        return "Bash", "sh"
    # Default to Python
    return "Python", "py"


def generate_code(query: str) -> str:
    """Call the AI to generate code for the given request."""
    client = get_client()
    lang, _ = detect_language(query)

    system = f"""You are an expert {lang} developer. 
Write only clean, working, well-commented code.
Do NOT include any explanation outside the code block.
Do NOT use markdown headers or extra text — just the raw code."""

    response = client.chat.completions.create(
        model=TASK_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": query}
        ],
        max_tokens=2000
    )
    raw = response.choices[0].message.content or ""
    # Strip markdown code fences if present
    raw = re.sub(r"^```[\w]*\n?", "", raw.strip())
    raw = re.sub(r"\n?```$", "", raw.strip())
    return raw.strip()


def open_file(filepath: str):
    """Open a file in VS Code, falling back to the system default."""
    try:
        subprocess.Popen(["code", filepath])
        return "VS Code"
    except FileNotFoundError:
        try:
            os.startfile(filepath)
            return "default editor"
        except:
            return None


def handle_code_task(query: str) -> str:
    """Generate code, save to file, and open it."""
    lang, ext = detect_language(query)
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"jarvis_{timestamp}.{ext}"
    filepath = os.path.join(OUTPUT_DIR, filename)

    code = generate_code(query)
    if not code:
        return f"I'm sorry Mr. Aryan, I could not generate the code."

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(code)

    editor = open_file(filepath)
    if editor:
        return (
            f"Done Mr. Aryan. I have written the {lang} code and saved it as {filename}. "
            f"I have opened it in {editor} for you."
        )
    else:
        return (
            f"Done Mr. Aryan. I have written the {lang} code and saved it at {filepath}."
        )


# ─── Script Execution ─────────────────────────────────────────

def handle_run_task(query: str) -> str:
    """Find the latest .py file in JarvisOutput and run it."""
    py_files = sorted(
        [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".py")],
        key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)),
        reverse=True
    )
    if not py_files:
        return "I could not find any script to run Mr. Aryan. Please ask me to write a script first."

    latest = os.path.join(OUTPUT_DIR, py_files[0])
    try:
        result = subprocess.run(
            [sys.executable, latest],
            capture_output=True, text=True, timeout=15
        )
        output = (result.stdout or result.stderr or "").strip()
        if not output:
            return f"The script ran successfully Mr. Aryan with no output."
        # Truncate very long output
        if len(output) > 300:
            output = output[:300] + "..."
        return f"Script ran successfully. Here is the output: {output}"
    except subprocess.TimeoutExpired:
        return "The script took too long and was stopped Mr. Aryan."
    except Exception as e:
        return f"There was an error running the script: {str(e)[:100]}"


# ─── Document Writing ─────────────────────────────────────────

def generate_document(query: str) -> str:
    """Call AI to generate a document/report/essay."""
    client = get_client()
    system = """You are a professional writer. 
Write a clear, well-structured document based on the user's request.
Use plain text only. No markdown, no bold, no special symbols."""

    response = client.chat.completions.create(
        model=TASK_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": query}
        ],
        max_tokens=2000
    )
    return (response.choices[0].message.content or "").strip()


def handle_document_task(query: str) -> str:
    """Generate and save a document."""
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"jarvis_doc_{timestamp}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)

    content = generate_document(query)
    if not content:
        return "I'm sorry Mr. Aryan, I could not generate the document."

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    open_file(filepath)
    return (
        f"Done Mr. Aryan. I have written the document and saved it as {filename}. "
        f"I have opened it for you."
    )


# ─── Main Entry Point ─────────────────────────────────────────

def handle_task(query: str) -> str:
    """Route query to the appropriate heavy task handler."""
    task_type = detect_task_type(query)
    if task_type == "run":
        return handle_run_task(query)
    elif task_type == "document":
        return handle_document_task(query)
    else:
        return handle_code_task(query)
