import yt_dlp
import sys
import json

def get_audio_url(youtube_url):
    # Konfigurasi murni ala Bot Discord (Lavalink)
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'cachedir': False,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return {
                "success": True,
                "stream_url": info.get('url'),
                # RAHASIA BOT DISCORD: Ambil headers asli dari YouTube!
                "headers": info.get('http_headers', {})
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_playlist_entries(playlist_url):
    ydl_opts = {'extract_flat': 'in_playlist', 'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            entries = info.get('entries', [])[:50]
            tracks = [{"title": e.get('title', 'Unknown'), "url": f"https://www.youtube.com/watch?v={e.get('id')}"} for e in entries if e]
            return {"success": True, "playlist_title": info.get('title', 'Playlist'), "tracks": tracks}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_youtube(query, limit=10):
    ydl_opts = {'extract_flat': True, 'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            entries = info.get('entries', [])
            tracks = [{"title": e.get('title', 'Unknown'), "url": f"https://www.youtube.com/watch?v={e.get('id')}"} for e in entries if e]
            return {"success": True, "tracks": tracks}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_home_feed():
    ydl_opts = {'extract_flat': True, 'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info("ytsearch12:trending music indonesia", download=False)
            entries = info.get('entries', [])
            tracks = [{"title": e.get('title', 'Unknown'), "url": f"https://www.youtube.com/watch?v={e.get('id')}", "thumbnail": f"https://i.ytimg.com/vi/{e.get('id')}/mqdefault.jpg"} for e in entries if e]
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
    
    # Cetak murni JSON tanpa sampah log
    print(json.dumps(output))