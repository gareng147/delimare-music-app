import yt_dlp
import sys
import json
import re
import urllib.request # Menggantikan requests agar anti-eror di Docker AWS

def get_video_id(url):
    # REGEX SAKTI: Mendeteksi ID dari link YouTube PC, HP (youtu.be), maupun Shorts
    pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)|watch\?.*v=|shorts/)|youtu\.be/)([^"&?/\s]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_audio_url(youtube_url):
    try:
        video_id = get_video_id(youtube_url)
        if not video_id:
            return {"success": False, "error": "Format Link YouTube tidak dikenali"}
        
        invidious_instance = "https://invidious.nerdvpn.de" 
        api_url = f"{invidious_instance}/api/v1/videos/{video_id}"
        
        # Menggunakan urllib bawaan Python agar tidak perlu install pip requests di AWS
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read()
            data = json.loads(html.decode('utf-8'))
        
        audio_streams = [f for f in data.get('adaptiveFormats', []) if f.get('type', '').startswith('audio/')]
        
        if audio_streams:
            stream_url = audio_streams[0].get('url')
            if stream_url.startswith("/"):
                stream_url = invidious_instance + stream_url
                
            return {
                "success": True,
                "title": data.get('title', 'Unknown Title'),
                "stream_url": stream_url,
                "duration": data.get('lengthSeconds', 0),
                "related_videos": [] 
            }
        return {"success": False, "error": "Audio format not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_playlist_entries(playlist_url):
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(playlist_url, download=False)
            entries = info_dict.get('entries', [])[:50]
            
            tracks = []
            for entry in entries:
                if entry and entry.get('id'):
                    tracks.append({
                        "title": entry.get('title', 'Unknown Title'),
                        "url": f"https://www.youtube.com/watch?v={entry.get('id')}"
                    })
            return {"success": True, "playlist_title": info_dict.get('title', 'Playlist'), "tracks": tracks}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_youtube(query, limit=10):
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            entries = info_dict.get('entries', [])
            tracks = []
            for entry in entries:
                if entry and entry.get('id'):
                    tracks.append({
                        "title": entry.get('title', 'Unknown Title'),
                        "url": f"https://www.youtube.com/watch?v={entry.get('id')}"
                    })
            return {"success": True, "tracks": tracks}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_home_feed():
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info("ytsearch12:trending music indonesia", download=False)
            entries = info_dict.get('entries', [])
            tracks = []
            for entry in entries:
                if entry and entry.get('id'):
                    tracks.append({
                        "title": entry.get('title', 'Unknown Title'),
                        "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "thumbnail": f"https://i.ytimg.com/vi/{entry.get('id')}/mqdefault.jpg"
                    })
            return {"success": True, "tracks": tracks}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stream"
    target = sys.argv[2] if len(sys.argv) > 2 else ""

    if mode == "playlist":
        output = get_playlist_entries(target)
    elif mode == "search":
        output = search_youtube(target)
    elif mode == "home":
        output = get_home_feed()
    else:
        output = get_audio_url(target)
        
    print(json.dumps(output))