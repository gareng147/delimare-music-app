import yt_dlp
import sys
import json

def get_audio_url(youtube_url):
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            
            # AMBIL 10 VIDEO TERKAIT (REKOMENDASI) DARI YOUTUBE
            related = info_dict.get('related_videos', [])
            related_tracks = []
            for v in related[:10]:
                if v.get('id'):
                    related_tracks.append({
                        "title": v.get('title', 'Unknown Title'),
                        "url": f"https://www.youtube.com/watch?v={v.get('id')}"
                    })
                    
            return {
                "success": True,
                "title": info_dict.get('title', 'Unknown Title'),
                "stream_url": info_dict.get('url', None),
                "duration": info_dict.get('duration', 0),
                "related_videos": related_tracks  # Kirim ke frontend
            }
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
    # MEMBUAT BERANDA: Mengambil musik yang sedang tren atau populer di Indonesia
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
                        "thumbnail": f"https://i.ytimg.com/vi/{entry.get('id')}/mqdefault.jpg" # Ambil gambar cover lagu
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