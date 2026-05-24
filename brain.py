import aiohttp
from config import OPENROUTER_API_KEY

class Brain:

    def __init__(self, voice=None):

        self.voice = voice

    async def think(self, query):

        try:

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Jarvis, a highly intelligent AI assistant "
                            "for Mr Aryan."
                        )
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:

                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:

                    result = await response.json()

                    return result["choices"][0]["message"]["content"]

        except Exception as e:

            return f"Brain error: {str(e)}"