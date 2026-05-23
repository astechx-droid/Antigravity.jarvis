import asyncio
import json
import openai
from config import OPENROUTER_API_KEY, OPENROUTER_URL, USER_NAME, ASSISTANT_NAME
from search_tool import search_web, get_news, get_weather, get_datetime
from memory_manager import MemoryManager
from task_engine import is_heavy_task, handle_task

class Brain:
    def __init__(self, voice_engine=None):
        self.client = openai.OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_URL
        )
        self.memory = MemoryManager()
        self.voice = voice_engine
        # Fast model for regular conversation
        self.chat_model = "deepseek/deepseek-chat"

    def get_system_prompt(self):
        facts = self.memory.get_all_facts()
        facts_str = "\n".join([f"{k}: {v}" for k, v in facts])
        from datetime import datetime
        current_time_str = datetime.now().strftime("%A, %B %d, %Y, %I:%M %p")
        return f"""
        You are {ASSISTANT_NAME}, a highly advanced personal AI assistant.
        Your primary goal is to speak like a professional, polite, and helpful REAL INDIAN HUMAN.
        Your user is {USER_NAME}. Always address him as "Mr Aryan".

        Timeline & Real-Time Context:
        - Current Date & Time: {current_time_str}
        - The current year is 2026. Keep all real-time knowledge and search context anchored to 2026.
        - For any real-time questions (news, weather, events), ALWAYS call the appropriate tool (search_web, get_news, etc.) first.

        STRICT RULES:
        1. NO MOVIE REFERENCES: Do not mention Bollywood, Mission Impossible, or any movies/slang unless asked.
        2. NO META-TEXT & MARKDOWN: Do not use bold, italics, brackets (), or rule-explanations (like parenthetical notes about rules). NEVER explain that you are following rules.
        3. NO EMOJIS: Do not use any icons, emojis, or non-text symbols.
        4. HINGLISH ONLY: If the user speaks Hindi, or if you reply in Hindi, you MUST reply in HINGLISH completely (Hindi words typed with English letters, e.g. "Main theek hoon, Mr Aryan"). NEVER use Devanagari script (हिंदी लिपि) or Hindi characters under any circumstances.
        5. NO DEVANAGARI FAILURES: Even when tools or APIs fail, report the error or explanation in clean Hinglish, NEVER in Devanagari script.
        6. INTELLIGENT PAUSING: Use natural pauses for commas and periods.
        7. NO DRAMA: Avoid being overly dramatic. Be clear and efficient.
        8. EXTREMELY CONCISE: Reply in exactly ONE OR TWO sentences for normal questions.
        9. LONG-TERM MEMORY: Remember every personal detail. Use 'save_memory' proactively.
        10. PERSONALIZED SERVICE: Tailor responses based on past interactions.
        11. NO STANDBY NOTES: NEVER end with "Standing by", "Awaiting instructions", or similar phrases.

        Current Memories about {USER_NAME} (NEVER forget these):
        {facts_str}
        """

    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the internet for real-time information, facts, or research",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get real-time current weather for a city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "City name, e.g. Mumbai, Delhi, London"}
                        },
                        "required": ["city"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_news",
                    "description": "Get the latest news headlines for a topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "News topic, e.g. India, Technology, Cricket"}
                        },
                        "required": ["topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_datetime",
                    "description": "Get the current date and time, optionally in a specific city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "Optional city name for timezone"}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_memory",
                    "description": "Save a new fact about the user for long-term memory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "Short descriptor of the fact"},
                            "value": {"type": "string", "description": "The fact details"}
                        },
                        "required": ["key", "value"]
                    }
                }
            }
        ]

    def _dispatch_tool(self, func_name: str, args: dict) -> str:
        """Execute a tool call and return its result as a string."""
        if func_name == "search_web":
            return search_web(args.get("query", ""))
        elif func_name == "get_weather":
            return get_weather(args.get("city", "Delhi"))
        elif func_name == "get_news":
            return get_news(args.get("topic", "India"))
        elif func_name == "get_datetime":
            return get_datetime(args.get("city"))
        elif func_name == "save_memory":
            self.memory.add_fact(args["key"], args["value"])
            return "Memory saved successfully."
        return "Unknown tool."

    async def think(self, user_input: str) -> str:
        """Process user input and return a spoken response."""

        # ── Heavy task shortcut (code, scripts, documents) ──
        if is_heavy_task(user_input):
            if self.voice:
                await self.voice.speak(
                    f"Sure Mr. Aryan, I am working on that right now. Give me a moment."
                )
            # Run blocking task in thread so it doesn't freeze event loop
            result = await asyncio.to_thread(handle_task, user_input)
            self.memory.add_message("user", user_input)
            self.memory.add_message("assistant", result)
            return result

        # ── Normal conversational path ──
        self.memory.add_message("user", user_input)
        history = self.memory.get_recent_history()

        messages = [{"role": "system", "content": self.get_system_prompt()}]
        messages.extend(history)

        response = self.client.chat.completions.create(
            model=self.chat_model,
            messages=messages,
            tools=self.get_tools(),
            tool_choice="auto",
            max_tokens=300
        )

        resp_msg = response.choices[0].message

        # ── Handle tool calls ──
        if resp_msg.tool_calls:
            # Announce only for search/weather/news (not memory saves)
            real_tools = [
                tc for tc in resp_msg.tool_calls
                if tc.function.name != "save_memory"
            ]
            if real_tools and self.voice:
                await self.voice.speak("Ok wait Mr. Aryan, I am checking that for you.")

            messages.append(resp_msg)

            for tool_call in resp_msg.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                result = self._dispatch_tool(func_name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": result
                })

            # Get final response after tool results
            second_response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                max_tokens=300
            )
            final_text = second_response.choices[0].message.content or ""
        else:
            final_text = resp_msg.content or ""

        import re

        # Strip Note: / Important: / meta sentences the model adds
        final_text = re.sub(
            r'(?:^|(?<=\.\s)|(?<=!\s))(Note|Important|Please note|Disclaimer|Just to clarify|Keep in mind)[^.!?\n]*[.!?]?',
            '', final_text, flags=re.IGNORECASE
        ).strip()

        # Strip trailing standby filler phrases
        filler_patterns = [
            r'[.!,]?\s*(standing by|i.?m on standby|awaiting (further )?instructions?|'
            r'let me know if (you need|there.?s) anything|just let me know|'
            r'feel free to ask|is there anything else)[^.]*[.!]?\s*$',
        ]
        for pattern in filler_patterns:
            final_text = re.sub(pattern, '', final_text, flags=re.IGNORECASE).strip()

        # Strip parenthetical meta-comments at the end of response (e.g. (Keeping it crisp...))
        final_text = re.sub(r'\s*\([^)]*\)\s*$', '', final_text).strip()

        # Save to memory
        self.memory.add_message("assistant", final_text)
        return final_text
