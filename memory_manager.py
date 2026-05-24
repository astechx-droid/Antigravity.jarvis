import sqlite3
from config import DB_PATH

class MemoryManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.setup_db()

    def setup_db(self):
        """Initializes tables for conversation history and long-term facts."""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_key TEXT UNIQUE,
                fact_val TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_message(self, role, content):
        """Adds a message to the history."""
        self.cursor.execute("INSERT INTO history (role, content) VALUES (?, ?)", (role, content))
        self.conn.commit()

    def get_recent_history(self, limit=10):
        """Fetches the last N messages for conversation context."""
        self.cursor.execute("SELECT role, content FROM history ORDER BY id DESC LIMIT ?", (limit,))
        rows = self.cursor.fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    def add_fact(self, key, val):
        """Stores a long-term memory fact."""
        self.cursor.execute("INSERT OR REPLACE INTO facts (fact_key, fact_val) VALUES (?, ?)", (key, val))
        self.conn.commit()

    def get_all_facts(self):
        """Fetches all long-term facts."""
        self.cursor.execute("SELECT fact_key, fact_val FROM facts")
        return self.cursor.fetchall()

    def clear_history(self):
        """Clears the short-term history."""
        self.cursor.execute("DELETE FROM history")
        self.conn.commit()

if __name__ == "__main__":
    memory = MemoryManager()
    memory.add_message("user", "Hello Jarvis")
    memory.add_message("assistant", "Hello Mr. Aryan")
    print(memory.get_recent_history())
