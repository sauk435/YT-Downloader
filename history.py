# history.py — Download history persistence

import json
import os
from datetime import datetime

def _get_history_file():
    app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
    data_dir = os.path.join(app_data, 'YouTube Downloader')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'history.json')

def _load():
    history_file = _get_history_file()
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def _save(data):
    history_file = _get_history_file()
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError:
        pass

def add_entry(title, url, file_path, format_type, quality='Auto'):
    """Add a download entry to history."""
    history = _load()
    entry = {
        'title': title,
        'url': url,
        'file_path': file_path,
        'format': format_type,
        'quality': quality,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
    history.insert(0, entry)  # newest first
    # Keep max 100 entries
    history = history[:100]
    _save(history)
    return entry

def get_history():
    """Return download history, newest first."""
    return _load()

def remove_entry(index):
    """Remove a specific entry by its index."""
    history = _load()
    if 0 <= index < len(history):
        history.pop(index)
        _save(history)

def clear_history():
    """Clear all download history."""
    _save([])
