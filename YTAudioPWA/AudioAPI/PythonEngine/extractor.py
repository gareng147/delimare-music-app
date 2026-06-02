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
        return {"success": False, "error": "URL tidak valid"}

    # JALUR BAWAH TANAH: Server API Indonesia (Kebal Blokir IP AWS)
    apis = [
        f"https://api.siputzx.my.id/api/d/ytmp3?url={youtube_url}",
        f"https://api.ryzendesu.vip/api/downloader/ytmp3?url={youtube_url}",
        f"https://api.vreden.my.id/api/ytmp3?url={youtube_url}"
    ]
    
    errors = []
    for api in apis:
        try:
            req = urllib.request.Request(api, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Ekstrak otomatis URL audio dari response JSON API
                urls = re.findall(r'(https?://[^\s\'"]+)', json.dumps(data))
                for u in urls:
                    if 'googlevideo.com' in u or '.mp3' in u or 'download' in u.lower() or 'dl' in u.lower():
                        return {"success": True, "stream_url": u}
        except Exception as e:
            errors.append(f"[{api.split('/')[2]} Down]")

    # FALLBACK TERAKHIR: yt-dlp Murni tanpa Kuki
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'skip_download': True,
        'cachedir': False
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return {"success": True, "stream_url": info.get('url')}
    except Exception as e:
        errors.append(f"[YT-DLP Blocked]")

    return {"success": False, "error": " | ".join(errors)}

# =========================================================
# YT-DLP MURNI UNTUK PENCARIAN (Aman dari pemblokiran bot AWS)
# =========================================================

def get_playlist_entries(playlist_url):
    ydl_opts = {'extract_flat': 'in_playlist', 'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(playlist_url, download=False)
            entries = info_dict.get('entries', [])[:50]
            tracks = [{"title": e.get('title', 'Unknown'), "url": f"https://www.youtube.com/watch?v={e.get('id')}"} for e in entries if e]
            return {"success": True, "playlist_title": info_dict.get('title', 'Playlist'), "tracks": tracks}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_youtube(query, limit=10):
    ydl_opts = {'extract_flat': True, 'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            entries = info_dict.get('entries', [])
            tracks = [{"title": e.get('title', 'Unknown'), "url": f"https://www.youtube.com/watch?v={e.get('id')}"} for e in entries if e]
            return {"success": True, "tracks": tracks}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_home_feed():
    ydl_opts = {'extract_flat': True, 'quiet': True, 'no_warnings': True}
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