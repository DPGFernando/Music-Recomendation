# 🎵 BioSync Music Server

A Python Flask server that receives emotional state data from the ESP32-S3 (via Wokwi simulation), searches YouTube Data API v3 for matching music, and displays song recommendations on a live browser dashboard and Blynk IoT dashboard.

---

## How It Works

```
ESP32-S3 (Wokwi Simulation)
        │
        │  HTTP POST /emotion  →  {"emotion": "CALM"}
        ▼
Music_Server.py  (runs on your PC — port 5000)
        │
        │  YouTube Data API v3 search query
        ▼
Google YouTube API
        │
        │  Returns: song titles, channel names, YouTube URLs
        ▼
Browser Dashboard  →  http://localhost:5000/songs
Blynk Dashboard    →  "Now Playing" widget (V6)
```

---

## Requirements

### Python Libraries
```bash
pip install flask requests
```

### Accounts and Keys Needed

| Service | Purpose | Link |
|---------|---------|------|
| Google Cloud | YouTube Data API v3 key | console.cloud.google.com |
| Wokwi | ESP32 simulation + IoT Gateway | wokwi.com |
| Blynk | IoT cloud dashboard | blynk.cloud |

### Additional Tools
- **Wokwi IoT Gateway** (`wokwigw.exe`) — download from:
  https://github.com/wokwi/wokwigw/releases

---

## Setup

### Step 1 — Get a YouTube API Key

1. Go to **console.cloud.google.com** and sign in
2. Create a new project named `BioSync`
3. Click **APIs & Services → Enable APIs and Services**
4. Search `YouTube Data API v3` → click **Enable**
5. Go to **Credentials → Create Credentials → API Key**
6. Copy the generated key
7. Click **Restrict Key → select YouTube Data API v3 → Save**

> ⚠️ Restricting the key is important — it prevents others from using your quota if the key is ever exposed.

### Step 2 — Add Your API Key to the Server

Open `Music_Server.py` and replace the placeholder on this line:

```python
YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"  # ← paste your key here
```

### Step 3 — Install Wokwi IoT Gateway

1. Download `wokwigw-windows-amd64.zip` from the releases page
2. Extract the ZIP to your Desktop
3. Double-click `wokwigw.exe` to run it
4. Confirm you see: **Listening on TCP port 9011**

---

## Running the Server

```bash
python Music_Server.py
```

You should see:

```
=======================================================
🎵 BioSync AIoT — YouTube Music Server
=======================================================
   POST http://localhost:5000/emotion  ← ESP32 sends here
   GET  http://localhost:5000/songs    ← open in browser
   GET  http://localhost:5000/status   ← health check
=======================================================
   Waiting for emotion data from ESP32-S3...
   Open browser: http://localhost:5000/songs
=======================================================
```

---

## Startup Order

Always follow this exact order:

```
1. Run wokwigw.exe            →  confirm "Listening on TCP port 9011"
2. Run python Music_Server.py →  confirm server starts on port 5000
3. Open your Wokwi project in browser
4. Press F1 in Wokwi editor → select "Enable Private Wokwi IoT Gateway"
5. Click the ▶ Play button in Wokwi to start simulation
6. Open http://localhost:5000/songs in your browser
```

---

## API Endpoints

### POST `/emotion`

Receives the detected emotion from ESP32-S3 and returns YouTube song recommendations.

**Request body:**
```json
{ "emotion": "CALM" }
```

**Supported values:** `CALM` · `STRESSED` · `HAPPY`

**Response:**
```json
{
  "status":    "success",
  "emotion":   "CALM",
  "genre":     "Ambient/Classical",
  "tempo":     "60-80 BPM",
  "song":      "Peaceful Piano Music",
  "channel":   "Relaxing Records",
  "url":       "https://www.youtube.com/watch?v=xxxxx",
  "all_songs": [
    { "title": "...", "channel": "...", "url": "..." },
    { "title": "...", "channel": "...", "url": "..." },
    { "title": "...", "channel": "...", "url": "..." }
  ]
}
```

---

### GET `/songs`

Browser dashboard showing current song recommendations with clickable YouTube links.

Open at: **http://localhost:5000/songs**

- Auto-refreshes every 10 seconds
- Colour-coded by emotion:
  - 🟢 Green — CALM
  - 🔴 Red — STRESSED
  - 🔵 Blue — HAPPY
- Each song has a direct **▶ Play on YouTube** link

---

### GET `/status`

Server health check — useful for debugging ESP32 connectivity.

**Response:**
```json
{
  "status": "BioSync server running ✅",
  "current_emotion": "CALM",
  "songs_count": 3
}
```

---

## Emotion to Music Mapping

Based on the Valence-Arousal model of music emotion (Eerola & Vuoskoski, 2021)
and EDA (electrodermal activity) levels from the WESAD dataset:

| Emotion | EDA Level | Music Genre | Tempo | YouTube Search Query |
|---------|-----------|-------------|-------|----------------------|
| HAPPY | Low (0.26 µS) | Pop/Upbeat | 100-130 BPM | upbeat pop happy feel good music |
| CALM | Medium (0.72 µS) | Ambient/Classical | 60-80 BPM | ambient classical relaxing music |
| STRESSED | High (1.99 µS) | Lo-fi/Meditation | 50-70 BPM | lofi chill meditation stress relief |

---

## Testing Without Wokwi

You can test the server directly from your PC:

**PowerShell:**
```powershell
Invoke-WebRequest `
  -Uri "http://localhost:5000/emotion" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"emotion":"CALM"}'
```

**Python:**
```python
import requests
response = requests.post(
    "http://localhost:5000/emotion",
    json={"emotion": "STRESSED"}
)
print(response.json())
```

When the server receives the request you will see in the terminal:

```
=======================================================
🎭 Emotion detected: STRESSED
🎵 Genre: Lo-fi/Meditation (50-70 BPM)
🔍 Searching YouTube...

📋 Recommendations:
   1. Lofi Hip Hop Radio — Beats to Study/Relax
      by Lofi Girl
      https://www.youtube.com/watch?v=xxxxx
   2. ...
   3. ...

🌐 View dashboard: http://localhost:5000/songs
```

---

## YouTube API Quota

The YouTube Data API v3 has a **free daily quota of 10,000 units**.
Each search request costs **100 units** — allowing up to 100 searches per day.

The server uses **caching** to reduce API calls:
- YouTube is only queried when the **emotion changes**
- Repeated detections of the same emotion reuse the cached results
- This reduces API usage by approximately **97%**

> ⚠️ If you see `❌ YouTube API error` in the terminal, your daily quota may be exceeded. Wait 24 hours or create a new restricted API key.

---

## Project File Structure

```
Music_Server.py       ← this file (Flask server + YouTube API)
README.md             ← this file

── Wokwi files ──────────────────────────────────
sketch.ino            ← ESP32-S3 Arduino firmware
tiny_weights2.h       ← Neural network weights (C float arrays)
diagram.json          ← Circuit wiring diagram
libraries.txt         ← Required Arduino libraries

── Training ──────────────────────────────────────
BioSync.ipynb         ← Google Colab ML training notebook
```

---

