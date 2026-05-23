# Deploy JARVIS on Render

Host the **web HUD** (`server.py`) on [Render](https://render.com). Voice desktop (`main.py`) stays on your PC only.

## What works on Render

| Feature | Cloud |
|---------|--------|
| Red JARVIS UI + animation | Yes |
| Chat API (`/chat`) | Yes |
| Browser mic + speech (HTTPS) | Yes |
| OpenRouter AI | Yes (API key required) |
| Web search / news | Yes (SerpAPI key optional) |
| SQLite memory | Yes (resets on redeploy unless you add a disk) |
| `main.py` voice / Edge TTS | No (run locally) |

## 1. Push code to GitHub

```bash
cd c:\Users\GVSCH\Downloads\jarvis
git init
git add .
git commit -m "Prepare Jarvis for Render"
git branch -M main
git remote add origin https://github.com/YOUR_USER/jarvis.git
git push -u origin main
```

Never commit `.env` — it is in `.gitignore`.

## 2. Create Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New +** → **Web Service**
2. Connect your GitHub repo
3. Settings:
   - **Name:** `jarvis` (or any name)
   - **Region:** closest to you
   - **Branch:** `main`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free (spins down after ~15 min idle; first load may be slow)

Or use **Blueprint**: **New +** → **Blueprint** → point at repo with `render.yaml`.

## 3. Environment variables

In Render → your service → **Environment**:

| Key | Required | Notes |
|-----|----------|--------|
| `OPENROUTER_API_KEY` | Yes | From [openrouter.ai](https://openrouter.ai) |
| `SERPAPI_API_KEY` | No | Search/news; copy from local `.env` if you use it |

Click **Save Changes** → Render redeploys.

## 4. Open your app

URL will look like:

`https://jarvis-xxxx.onrender.com`

- Allow **microphone** when prompted (HTTPS is required; Render provides it).
- Tap the screen once to start listening.
- Say **"Hey Jarvis"**.

## 5. Android phone

Open the same `https://....onrender.com` URL in Chrome → **Add to Home screen**.

No PC needed after deploy (unless you want local `main.py` voice).

## Free tier notes

- **Cold start:** ~30–60 s after idle; show a loading message if needed.
- **Memory DB:** `jarvis_memory.db` is wiped on each deploy; use [Render Disk](https://render.com/docs/disks) on paid plan for persistence.
- **Secrets:** only set keys in Render dashboard, not in code.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build fails | Check `requirements.txt` and Python `runtime.txt` |
| 502 on chat | Set `OPENROUTER_API_KEY` in Environment |
| Mic not working | Use HTTPS URL; allow mic in browser |
| COMMS OFFLINE | Wait for deploy; check Render **Logs** tab |
