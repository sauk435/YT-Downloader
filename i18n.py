# i18n.py — Multi-language support (EN/ES)

_current_lang = 'en'

_strings = {
    # App
    'app_title': {'en': 'YouTube Downloader', 'es': 'Descargador de YouTube'},
    
    # Search
    'search_placeholder': {'en': 'Search videos or paste YouTube URL...', 'es': 'Buscar videos o pegar URL de YouTube...'},
    'search_btn': {'en': 'Search', 'es': 'Buscar'},
    'searching': {'en': 'Searching...', 'es': 'Buscando...'},
    'results_found': {'en': '{n} results found.', 'es': '{n} resultados encontrados.'},
    'no_results': {'en': 'No videos found.', 'es': 'No se encontraron videos.'},
    'search_results': {'en': 'Search Results', 'es': 'Resultados de búsqueda'},
    
    # Video
    'select': {'en': 'Select', 'es': 'Seleccionar'},
    'preview': {'en': 'Preview', 'es': 'Ver'},
    'selected': {'en': 'Selected: {title}', 'es': 'Seleccionado: {title}'},
    'add_to_queue': {'en': 'Add to Queue', 'es': 'Añadir a cola'},
    
    # Details panel
    'show_details': {'en': 'Show Details', 'es': 'Ver detalles'},
    'hide_details': {'en': 'Hide Details', 'es': 'Ocultar detalles'},
    'channel': {'en': 'Channel', 'es': 'Canal'},
    'views': {'en': 'Views', 'es': 'Vistas'},
    'upload_date': {'en': 'Upload Date', 'es': 'Fecha de subida'},
    'likes': {'en': 'Likes', 'es': 'Me gusta'},
    'description': {'en': 'Description', 'es': 'Descripción'},
    
    # Trim
    'trim_label': {'en': 'Trim (drag handles to set start and end):', 'es': 'Recortar (arrastra los handles para inicio y fin):'},
    'enable_trim': {'en': 'Enable trim', 'es': 'Activar recorte'},
    
    # Options
    'format': {'en': 'Format:', 'es': 'Formato:'},
    'video_mp4': {'en': 'Video (MP4)', 'es': 'Video (MP4)'},
    'audio_mp3': {'en': 'Audio (MP3)', 'es': 'Audio (MP3)'},
    'quality': {'en': 'Quality:', 'es': 'Calidad:'},
    'folder': {'en': 'Folder', 'es': 'Carpeta'},
    'estimated_size': {'en': 'Estimated: ~{size}', 'es': 'Estimado: ~{size}'},
    
    # Download
    'download': {'en': 'Download', 'es': 'Descargar'},
    'download_all': {'en': 'Download All', 'es': 'Descargar todo'},
    'starting_download': {'en': 'Starting download...', 'es': 'Iniciando descarga...'},
    'downloading': {'en': 'Downloading: {percent:.1f}% ({speed})', 'es': 'Descargando: {percent:.1f}% ({speed})'},
    'download_complete': {'en': 'Download complete!', 'es': '¡Descarga completada!'},
    'download_error': {'en': 'Download error.', 'es': 'Error en la descarga.'},
    'success': {'en': 'Success', 'es': 'Éxito'},
    'success_msg': {'en': 'Download finished successfully.', 'es': 'Descarga finalizada correctamente.'},
    'error': {'en': 'Error', 'es': 'Error'},
    'error_msg': {'en': 'An error occurred:\n{msg}', 'es': 'Ocurrió un error:\n{msg}'},
    'warning': {'en': 'Warning', 'es': 'Aviso'},
    'select_video_first': {'en': 'Please select a video first.', 'es': 'Por favor selecciona un video primero.'},
    'ready': {'en': 'Ready', 'es': 'Esperando'},
    
    # Queue
    'queue': {'en': 'Queue', 'es': 'Cola'},
    'queue_title': {'en': 'Download Queue', 'es': 'Cola de descargas'},
    'queue_empty': {'en': 'Queue is empty', 'es': 'Cola vacía'},
    'waiting': {'en': 'Waiting...', 'es': 'Esperando...'},
    'completed': {'en': 'Completed', 'es': 'Completado'},
    'failed': {'en': 'Failed', 'es': 'Error'},
    'clear_queue': {'en': 'Clear Completed', 'es': 'Limpiar completados'},
    
    # History
    'history': {'en': 'History', 'es': 'Historial'},
    'history_title': {'en': 'Download History', 'es': 'Historial de descargas'},
    'no_history': {'en': 'No downloads yet.', 'es': 'Aún no hay descargas.'},
    'clear_history': {'en': 'Clear List (Keep files)', 'es': 'Limpiar lista (Conservar archivos)'},
    'open_file': {'en': 'Open', 'es': 'Abrir'},
    'open_folder': {'en': 'Open Folder', 'es': 'Abrir carpeta'},
    'remove_entry': {'en': 'Remove from list', 'es': 'Quitar de la lista'},
    'delete_file': {'en': 'Delete File', 'es': 'Borrar archivo'},
    'confirm_delete': {'en': 'Are you sure you want to delete this file from your computer?', 'es': '¿Estás seguro de que quieres borrar este archivo de tu disco duro?'},
    
    # Settings
    'language': {'en': 'Language:', 'es': 'Idioma:'},
    'theme': {'en': 'Theme', 'es': 'Tema'},
    'use_cookies': {'en': 'Use Browser Cookies (Bypass blocks)', 'es': 'Usar Cookies del navegador (Saltar bloqueos)'},
    
    # Tray
    'show_window': {'en': 'Show', 'es': 'Mostrar'},
    'quit': {'en': 'Quit', 'es': 'Salir'},
    'tray_download_done': {'en': 'Download finished: {title}', 'es': 'Descarga finalizada: {title}'},
    
    # Playlist
    'playlist_detected': {'en': 'Playlist detected: {count} videos', 'es': 'Playlist detectada: {count} videos'},
    'select_all': {'en': 'Select All', 'es': 'Seleccionar todo'},
    'deselect_all': {'en': 'Deselect All', 'es': 'Deseleccionar todo'},
}

def set_language(lang):
    global _current_lang
    if lang in ('en', 'es'):
        _current_lang = lang

def get_language():
    return _current_lang

def t(key, **kwargs):
    """Get translated string by key, with optional format kwargs."""
    entry = _strings.get(key, {})
    text = entry.get(_current_lang, entry.get('en', f'[{key}]'))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
