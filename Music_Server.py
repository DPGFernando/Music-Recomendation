from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

YOUTUBE_API_KEY = "AIzaSyDCBoK61x6Y6AgvK3ato4Ogzpt4Z4DB074"  

# Emotion to music genre mapping 
EMOTION_CONFIG = {
    "CALM": {
        "query": "ambient classical relaxing music no copyright",
        "genre": "Ambient/Classical",
        "tempo": "60-80 BPM"
    },
    "STRESSED": {
        "query": "lofi chill meditation stress relief music",
        "genre": "Lo-fi/Meditation",
        "tempo": "50-70 BPM"
    },
    "HAPPY": {
        "query": "upbeat pop happy feel good music no copyright",
        "genre": "Pop/Upbeat",
        "tempo": "100-130 BPM"
    }
}

# Server state 
current_emotion = None
current_songs   = []


def search_youtube(emotion):
    """Search YouTube Data API v3 for music matching emotion"""
    config = EMOTION_CONFIG[emotion]
    url    = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part":            "snippet",
        "q":               config["query"],
        "type":            "video",
        "videoCategoryId": "10",        # Music category
        "videoEmbeddable": "true",
        "maxResults":      3,
        "key":             YOUTUBE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data     = response.json()

        if "error" in data:
            print(f"❌ YouTube API error: {data['error']['message']}")
            return []

        songs = []
        if "items" in data:
            for item in data["items"]:
                video_id = item["id"]["videoId"]
                title    = item["snippet"]["title"]
                channel  = item["snippet"]["channelTitle"]
                songs.append({
                    "title":   title,
                    "channel": channel,
                    "url":     f"https://www.youtube.com/watch?v={video_id}"
                })
        return songs

    except Exception as e:
        print(f"❌ YouTube search error: {e}")
        return []


@app.after_request
def add_headers(response):
    """Allow cross-origin requests"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/emotion', methods=['POST'])
def receive_emotion():
    """
    Receive emotion from ESP32-S3 or test client
    Returns YouTube music recommendations
    """
    global current_emotion, current_songs

    data    = request.json
    emotion = data.get('emotion', '').upper()

    if emotion not in EMOTION_CONFIG:
        return jsonify({"error": f"Unknown emotion: {emotion}"}), 400

    config = EMOTION_CONFIG[emotion]

    # Only search YouTube when emotion changes
    if emotion != current_emotion:
        current_emotion = emotion
        print(f"\n{'='*55}")
        print(f"🎭 Emotion detected: {emotion}")
        print(f"🎵 Genre: {config['genre']} ({config['tempo']})")
        print(f"🔍 Searching YouTube...")

        current_songs = search_youtube(emotion)

        if current_songs:
            print(f"\n📋 Recommendations:")
            for i, song in enumerate(current_songs):
                print(f"   {i+1}. {song['title']}")
                print(f"      by {song['channel']}")
                print(f"      {song['url']}")
            print(f"\n🌐 View dashboard: http://localhost:5000/songs")
        else:
            print("   ❌ No songs found — check API key!")

    # Return top song
    top_song = current_songs[0] if current_songs else {
        "title":   config['genre'] + " Music",
        "channel": "YouTube Music",
        "url":     ""
    }

    return jsonify({
        "status":    "success",
        "emotion":   emotion,
        "genre":     config['genre'],
        "tempo":     config['tempo'],
        "song":      top_song['title'],
        "channel":   top_song['channel'],
        "url":       top_song['url'],
        "all_songs": current_songs
    })


@app.route('/songs', methods=['GET'])
def get_songs():
    """
    Web dashboard — open in browser to see recommendations
    Auto-refreshes every 10 seconds
    """
    if not current_emotion:
        return """
        <html>
        <head>
            <title>BioSync Music</title>
            <style>
                body { font-family: Arial; background:#1a1a2e;
                       color:white; padding:40px; text-align:center; }
                h1   { color:#00d4ff; }
            </style>
        </head>
        <body>
            <h1>🎵 BioSync AIoT Music Server</h1>
            <p>Waiting for emotion data...</p>
            <p>Send a POST request to /emotion to get started.</p>
        </body>
        </html>
        """

    # Emotion colour mapping
    colors = {
        "CALM":     "#23C48E",
        "STRESSED": "#D3435C",
        "HAPPY":    "#04C0F8"
    }
    color = colors.get(current_emotion, "#ffffff")

    html = f"""
    <html>
    <head>
        <title>BioSync Music Recommendations</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body  {{ font-family: Arial; background:#1a1a2e;
                     color:white; padding:30px; margin:0; }}
            h1    {{ color:#00d4ff; text-align:center; }}
            .emotion {{ font-size:2.5em; text-align:center;
                        color:{color}; margin:10px 0; }}
            .genre {{ text-align:center; color:#888;
                      font-size:1.1em; margin-bottom:20px; }}
            .song {{ background:#16213e; padding:15px; margin:12px 0;
                     border-radius:10px;
                     border-left:5px solid {color}; }}
            .song-title {{ font-size:1.1em; font-weight:bold; }}
            .song-channel {{ color:#888; font-size:0.9em; margin:5px 0; }}
            .song a {{ color:#00d4ff; text-decoration:none;
                       font-size:0.95em; }}
            .song a:hover {{ text-decoration:underline; }}
            .footer {{ text-align:center; color:#444;
                       margin-top:30px; font-size:0.8em; }}
        </style>
    </head>
    <body>
        <h1>🎵 BioSync AIoT Music Recommendations</h1>
        <div class="emotion">● {current_emotion}</div>
        <div class="genre">
            {EMOTION_CONFIG[current_emotion]['genre']} |
            {EMOTION_CONFIG[current_emotion]['tempo']}
        </div>
        <h2>🎧 Recommended Songs:</h2>
    """

    for i, song in enumerate(current_songs):
        html += f"""
        <div class="song">
            <div class="song-title">{i+1}. {song['title']}</div>
            <div class="song-channel">by {song['channel']}</div>
            <a href="{song['url']}" target="_blank">▶ Play on YouTube</a>
        </div>
        """

    html += """
        <div class="footer">
            Auto-refreshes every 10 seconds |
            BioSync AIoT — MSc AI for IoT Project
        </div>
    </body>
    </html>
    """
    return html


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status":          "BioSync server running ✅",
        "current_emotion": current_emotion,
        "songs_count":     len(current_songs)
    })

# Entry point 
if __name__ == '__main__':
    print("=" * 55)
    print("🎵 BioSync AIoT — YouTube Music Server")
    print("=" * 55)
    print("   POST http://localhost:5000/emotion")
    print("   GET  http://localhost:5000/songs")
    print("=" * 55)
    print("   Waiting for emotion data...")
    print("   Open browser: http://localhost:5000/songs")
    print("=" * 55)
    app.run(host='0.0.0.0', port=5000, debug=False)