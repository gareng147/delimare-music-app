import yt_dlp
import sys
import json
import re
import urllib.request

def get_video_id(url):
    pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)|watch\?.*v=|shorts/)|youtu\.be/)([^"&?/\s]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_audio_url(youtube_url):
    video_id = get_video_id(youtube_url)
    if not video_id:
        return {"success": False, "error": "Format Link YouTube tidak dikenali"}
    
    # 3 Server Invidious Terkuat di Dunia sebagai jaringan cadangan
    invidious_instances = [
        "https://yewtu.be",
        "https://invidious.perennialte.ch",
        "https://inv.tux.digital"
    ]
    
    for instance in invidious_instances:
        try:
            api_url = f"{instance}/api/v1/videos/{video_id}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            audio_streams = [f for f in data.get('adaptiveFormats', []) if f.get('type', '').startswith('audio/')]
            
            if audio_streams:
                stream_url = audio_streams[0].get('url')
                if stream_url.startswith("/"):
                    stream_url = instance + stream_url
                    
                return {
                    "success": True,
                    "title": data.get('title', 'Unknown Title'),
                    "stream_url": stream_url
                }
        except Exception:
            continue # Jika server ini bermasalah/down, otomatis skip dan coba server berikutnya
            
    return {"success": False, "error": "Semua server proxy sedang sibuk. Silakan coba lagi nanti."}

def get_playlist_entries(playlist_url):
    ydl_opts = {'extract_flat': 'in_playlist', 'quiet': True, 'no_warnings': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(playlist_url, download=False)
            entries = info_dict.get('entries', [])[:50]
            tracks = [{"title": e.get('title', 'Unknown'), "url": f"https://www.youtube.com/watch?v={e.get('id')}"} for e in entries if e]
            return {"success": True, "playlist_title": info_dict.get('title', 'Playlist'), "tracks": tracks}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_youtube(query, limit=10):
    ydl_opts = {'extract_flat': True, 'quiet': True, 'no_warnings': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            entries = info_dict.get('entries', [])
            tracks = [{"title": e.get('title', 'Unknown'), "url": f"https://www.youtube.com/watch?v={e.get('id')}"} for e in entries if e]
            return {"success": True, "tracks": tracks}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_home_feed():
    ydl_opts = {'extract_flat': True, 'quiet': True, 'no_warnings': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info("ytsearch12:trending music indonesia", download=False)
            entries = info_dict.get('entries', [])
            tracks = [{
                "title": e.get('title', 'Unknown'),
                "url": f"https://www.youtube.com/watch?v={e.get('id')}",
                "thumbnail": f"https://i.ytimg.com/vi/{e.get('id')}/mqdefault.jpg"
            } for e in entries if e]
            return {"success": True, "tracks": tracks}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stream"
    target = sys.argv[2] if len(sys.argv) > 2 else ""
    if mode == "playlist": output = get_playlist_entries(target)
    elif mode == "search": output = search_youtube(target)
    elif mode == "home": output = get_home_feed()
    else: output = get_audio_url(target)
    print(json.dumps(output))