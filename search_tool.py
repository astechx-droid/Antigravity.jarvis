import requests
from datetime import datetime
from config import SERPAPI_API_KEY

# ─── Web Search ───────────────────────────────────────────────

def search_web(query):
    """Search the web and return top snippets using SerpAPI."""
    if not SERPAPI_API_KEY or "your_key_here" in SERPAPI_API_KEY:
        return "Search failed: SERPAPI_API_KEY is not set in your .env file."
    try:
        params = {
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "engine": "google"
        }
        resp = requests.get("https://serpapi.com/search", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        snippets = []
        if "answer_box" in data and "answer" in data["answer_box"]:
            snippets.append(f"Direct Answer: {data['answer_box']['answer']}")
        elif "answer_box" in data and "snippet" in data["answer_box"]:
            snippets.append(f"Direct Answer: {data['answer_box']['snippet']}")

        if "organic_results" in data:
            for r in data["organic_results"][:4]:
                snippets.append(f"{r.get('title', '')}: {r.get('snippet', '')}")
                
        return "\n".join(snippets) if snippets else "No results found."
    except Exception as e:
        return f"Search failed: {e}"

# ─── Weather ──────────────────────────────────────────────────

def get_weather(city="Delhi"):
    """Get real-time weather using wttr.in (no API key needed)."""
    try:
        city_encoded = city.strip().replace(" ", "+")
        url = f"https://wttr.in/{city_encoded}?format=3"
        resp = requests.get(url, timeout=6)
        if resp.status_code == 200:
            return resp.text.strip()
        return f"Could not fetch weather for {city}."
    except Exception as e:
        return f"Weather error: {e}"

# ─── News ─────────────────────────────────────────────────────

def get_news(topic="India"):
    """Get latest news headlines via SerpAPI."""
    if not SERPAPI_API_KEY or "your_key_here" in SERPAPI_API_KEY:
        return "News fetching failed: SERPAPI_API_KEY is not set in your .env file."
    try:
        params = {
            "q": topic,
            "api_key": SERPAPI_API_KEY,
            "engine": "google",
            "tbm": "nws"
        }
        resp = requests.get("https://serpapi.com/search", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if "news_results" not in data or not data["news_results"]:
            return "No news found."
            
        headlines = []
        for r in data["news_results"][:5]:
            headlines.append(f"{r.get('title', '')} — {r.get('source', '')}")
        return "\n".join(headlines)
    except Exception as e:
        return f"News error: {e}"

# ─── Date & Time ──────────────────────────────────────────────

def get_datetime(city=None):
    """Return current date and time. Optionally for a specific city/timezone."""
    try:
        if city:
            import pytz
            # Map common city names to timezone strings
            city_tz_map = {
                "new york": "America/New_York",
                "london": "Europe/London",
                "dubai": "Asia/Dubai",
                "delhi": "Asia/Kolkata",
                "mumbai": "Asia/Kolkata",
                "paris": "Europe/Paris",
                "tokyo": "Asia/Tokyo",
                "sydney": "Australia/Sydney",
                "la": "America/Los_Angeles",
                "los angeles": "America/Los_Angeles",
                "chicago": "America/Chicago",
                "beijing": "Asia/Shanghai",
                "singapore": "Asia/Singapore",
            }
            tz_name = city_tz_map.get(city.lower().strip())
            if tz_name:
                tz = pytz.timezone(tz_name)
                now = datetime.now(tz)
                return now.strftime(f"In {city.title()}, it's %I:%M %p on %A, %d %B %Y.")
            else:
                # Try pytz lookup directly
                tz = pytz.timezone(city)
                now = datetime.now(tz)
                return now.strftime(f"In {city}, it's %I:%M %p on %A, %d %B %Y.")
        else:
            now = datetime.now()
            return now.strftime("It's %I:%M %p on %A, %d %B %Y.")
    except Exception:
        now = datetime.now()
        return now.strftime("It's %I:%M %p on %A, %d %B %Y.")

# ─── Test ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("--- Web Search ---")
    print(search_web("latest AI news 2025"))
    print("\n--- Weather ---")
    print(get_weather("Mumbai"))
    print("\n--- News ---")
    print(get_news("India"))
    print("\n--- DateTime ---")
    print(get_datetime())
    print(get_datetime("London"))
