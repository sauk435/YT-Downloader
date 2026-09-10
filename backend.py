# backend.py — Core YouTube download logic

import os
import yt_dlp
import imageio_ffmpeg
import threading
import subprocess
import re
import shutil

# FFmpeg setup
_FFMPEG_ORIG = imageio_ffmpeg.get_ffmpeg_exe()
_FFMPEG_DIR = os.path.dirname(_FFMPEG_ORIG)
FFMPEG_EXE = os.path.join(_FFMPEG_DIR, 'ffmpeg.exe')
if not os.path.exists(FFMPEG_EXE):
    try:
        shutil.copy2(_FFMPEG_ORIG, FFMPEG_EXE)
    except Exception:
        FFMPEG_EXE = _FFMPEG_ORIG


def is_youtube_url(text):
    """Check if text is a YouTube URL."""
    patterns = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=',
        r'(https?://)?(www\.)?youtu\.be/',
        r'(https?://)?(www\.)?youtube\.com/shorts/',
    ]
    return any(re.search(p, text) for p in patterns)


def is_playlist_url(text):
    """Check if text is a YouTube playlist URL."""
    patterns = [
        r'(https?://)?(www\.)?youtube\.com/playlist\?list=',
        r'[?&]list=',
    ]
    return any(re.search(p, text) for p in patterns)


def _format_duration(duration):
    """Format seconds to readable time string."""
    if not duration:
        return "Unknown"
    mins, secs = divmod(int(duration), 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02}:{mins:02}:{secs:02}"
    return f"{mins:02}:{secs:02}"


def _format_number(n):
    """Format large numbers with K/M suffix."""
    if n is None:
        return "N/A"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _format_size(bytes_size):
    """Format bytes to human-readable size."""
    if not bytes_size:
        return "Unknown"
    if bytes_size >= 1_073_741_824:
        return f"{bytes_size / 1_073_741_824:.1f} GB"
    if bytes_size >= 1_048_576:
        return f"{bytes_size / 1_048_576:.1f} MB"
    return f"{bytes_size / 1024:.1f} KB"


def get_quality_format_string(quality='Auto', format_type='mp4'):
    """Map quality choice to yt-dlp format string."""
    if format_type == 'mp3':
        return 'bestaudio/best'

    quality_map = {
        'Auto': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '360p': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]',
        '480p': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]',
        '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
        '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]',
        '4K': 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]',
    }
    return quality_map.get(quality, quality_map['Auto'])


def search_videos(query, max_results=10, cookies_browser=None):
    """Search YouTube or extract info from a direct URL."""
    if is_youtube_url(query) and not is_playlist_url(query):
        try:
            return get_video_info(query, cookies_browser)
        except Exception as e:
            print(f"Error extracting URL info: {e}")
            return []

    ydl_opts = {
        'extract_flat': 'in_playlist',
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web', 'ios']}}
    }
    if cookies_browser:
        ydl_opts['cookiesfrombrowser'] = (cookies_browser.lower(),)
        
    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    vid_id = entry.get('id')
                    results.append({
                        'id': vid_id,
                        'url': entry.get('url') or f"https://www.youtube.com/watch?v={vid_id}",
                        'title': entry.get('title', 'Untitled'),
                        'duration': entry.get('duration'),
                        'duration_str': _format_duration(entry.get('duration')),
                        'thumbnail': f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg" if vid_id else None,
                    })
        except Exception as e:
            print(f"Search error: {e}")

    return results


def get_video_info(url, cookies_browser=None):
    """Extract basic video info from a direct URL."""
    ydl_opts = {
        'skip_download': True, 
        'quiet': True, 
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web', 'ios']}}
    }
    if cookies_browser:
        ydl_opts['cookiesfrombrowser'] = (cookies_browser.lower(),)
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        thumbnail = None
        for t in info.get('thumbnails', []):
            if t.get('url'):
                thumbnail = t['url']
        return [{
            'id': info.get('id'),
            'url': info.get('webpage_url') or url,
            'title': info.get('title', 'Untitled'),
            'duration': info.get('duration'),
            'duration_str': _format_duration(info.get('duration')),
            'thumbnail': thumbnail,
        }]


def get_full_video_info(url, cookies_browser=None):
    """Get detailed video info: channel, views, date, likes, description, formats."""
    ydl_opts = {
        'skip_download': True, 
        'quiet': True, 
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web', 'ios']}}
    }
    if cookies_browser:
        ydl_opts['cookiesfrombrowser'] = (cookies_browser.lower(),)
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        upload_date = info.get('upload_date', '')
        if upload_date and len(upload_date) == 8:
            upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

        return {
            'channel': info.get('uploader') or info.get('channel') or 'Unknown',
            'views': _format_number(info.get('view_count')),
            'views_raw': info.get('view_count'),
            'upload_date': upload_date or 'Unknown',
            'likes': _format_number(info.get('like_count')),
            'likes_raw': info.get('like_count'),
            'description': (info.get('description') or '')[:500],
            'formats': info.get('formats', []),
        }


def get_playlist_videos(url, cookies_browser=None):
    """Extract all videos from a YouTube playlist."""
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web', 'ios']}}
    }
    if cookies_browser:
        ydl_opts['cookiesfrombrowser'] = (cookies_browser.lower(),)
        
    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            entries = info.get('entries', [])
            for entry in entries:
                vid_id = entry.get('id')
                if not vid_id:
                    continue
                results.append({
                    'id': vid_id,
                    'url': entry.get('url') or f"https://www.youtube.com/watch?v={vid_id}",
                    'title': entry.get('title', 'Untitled'),
                    'duration': entry.get('duration'),
                    'duration_str': _format_duration(entry.get('duration')),
                    'thumbnail': f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg" if vid_id else None,
                })
        except Exception as e:
            print(f"Playlist error: {e}")
    return results


def estimate_file_size(url, format_type='mp4', quality='Auto', cookies_browser=None):
    """Estimate download file size. Returns human-readable string."""
    try:
        fmt = get_quality_format_string(quality, format_type)
        ydl_opts = {
            'format': fmt,
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web', 'ios']}}
        }
        if cookies_browser:
            ydl_opts['cookiesfrombrowser'] = (cookies_browser.lower(),)
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # Try requested_formats first (for merged formats)
            total = 0
            rf = info.get('requested_formats', [])
            if rf:
                for f in rf:
                    total += f.get('filesize') or f.get('filesize_approx') or 0
            else:
                total = info.get('filesize') or info.get('filesize_approx') or 0
            return _format_size(total) if total > 0 else "Unknown"
    except Exception:
        return "Unknown"


def _sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '_', name)


def _trim_with_ffmpeg(input_path, output_path, start_seconds, end_seconds):
    cmd = [FFMPEG_EXE, '-y', '-i', input_path]
    if start_seconds is not None:
        cmd += ['-ss', str(start_seconds)]
    if end_seconds is not None:
        cmd += ['-to', str(end_seconds)]
    cmd += ['-c', 'copy', output_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr[-500:]}")


def download_video(url, output_path, format_type='mp4', quality='Auto',
                   start_time=None, end_time=None,
                   progress_callback=None, speed_callback=None,
                   completion_callback=None, error_callback=None, cookies_browser=None):
    """
    Download a YouTube video.
    progress_callback(percent): called with download percentage
    speed_callback(speed_str): called with human-readable speed string
    """
    def _download_thread():
        try:
            need_trim = (start_time is not None) or (end_time is not None)

            if need_trim:
                import tempfile
                dl_dir = tempfile.mkdtemp(prefix="ytdl_")
            else:
                dl_dir = output_path

            fmt = get_quality_format_string(quality, format_type)
            ydl_opts = {
                'outtmpl': os.path.join(dl_dir, '%(title)s.%(ext)s'),
                'ffmpeg_location': os.path.dirname(FFMPEG_EXE),
                'format': fmt,
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {'youtube': {'player_client': ['android', 'web', 'ios']}}
            }
            if cookies_browser:
                ydl_opts['cookiesfrombrowser'] = (cookies_browser.lower(),)

            if format_type == 'mp3':
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                ydl_opts['merge_output_format'] = 'mp4'

            def progress_hook(d):
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate')
                    downloaded = d.get('downloaded_bytes', 0)
                    if total and total > 0:
                        percent = (downloaded / total) * 100
                        if progress_callback:
                            progress_callback(min(percent, 95 if need_trim else 100))
                    
                    speed = d.get('speed')
                    if speed and speed_callback:
                        if speed >= 1_048_576:
                            speed_callback(f"{speed / 1_048_576:.1f} MB/s")
                        elif speed >= 1024:
                            speed_callback(f"{speed / 1024:.1f} KB/s")
                        else:
                            speed_callback(f"{speed:.0f} B/s")

            ydl_opts['progress_hooks'] = [progress_hook]

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = _sanitize_filename(info.get('title', 'video'))
                final_file = ydl.prepare_filename(info)
                if format_type == 'mp3':
                    final_file = os.path.splitext(final_file)[0] + '.mp3'

            if need_trim:
                ext = 'mp3' if format_type == 'mp3' else 'mp4'
                downloaded_files = [f for f in os.listdir(dl_dir) if f.endswith(f'.{ext}')]
                if not downloaded_files:
                    downloaded_files = [f for f in os.listdir(dl_dir) if os.path.isfile(os.path.join(dl_dir, f))]
                if not downloaded_files:
                    raise FileNotFoundError("Downloaded file not found for trimming.")

                input_file = os.path.join(dl_dir, downloaded_files[0])
                output_file = os.path.join(output_path, f"{title}_trimmed.{ext}")

                if progress_callback:
                    progress_callback(96)
                _trim_with_ffmpeg(input_file, output_file, start_time, end_time)
                final_file = output_file

                try:
                    os.remove(input_file)
                    os.rmdir(dl_dir)
                except Exception:
                    pass

            if progress_callback:
                progress_callback(100)
            if completion_callback:
                try:
                    completion_callback(title, final_file)
                except TypeError:
                    completion_callback(title)

        except Exception as e:
            if error_callback:
                error_callback(str(e))

    threading.Thread(target=_download_thread, daemon=True).start()
