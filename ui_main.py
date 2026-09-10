# ui_main.py — Main window layout and interactions

import os
import sys
import json
import threading
import io
import webbrowser
import requests
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# Import third party
import windnd

# Import project modules
from i18n import t, set_language, get_language
from backend import search_videos, is_playlist_url, get_playlist_videos, estimate_file_size, download_video
from download_manager import DownloadManager, DownloadJob
from history import add_entry, get_history, clear_history
from tray import TrayManager
from ui_widgets import RangeSlider, DetailsPanel, QueuePanel

def is_portable():
    """Check if running as the portable executable."""
    exe_name = os.path.basename(sys.executable).lower()
    return 'portable' in exe_name

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def _get_config_file():
    app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
    data_dir = os.path.join(app_data, 'YouTube Downloader')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'config.json')

# Settings persistence
CONFIG_FILE = _get_config_file()

def load_config():
    default_config = {
        'theme': 'dark',
        'language': 'es',
        'download_path': os.path.expanduser("~\\Downloads"),
        'use_cookies': False,
        'cookies_browser': 'Chrome'
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                default_config.update(loaded)
        except Exception:
            pass
    return default_config

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Load config
        self.config = load_config()
        set_language(self.config['language'])
        ctk.set_appearance_mode(self.config['theme'])
        ctk.set_default_color_theme("blue")
        
        self.title(t('app_title'))
        self.geometry("1000x800")
        self.minsize(800, 700)
        
        # Tray setup — Only for installed version (background downloading when closed)
        if not is_portable():
            self.tray = TrayManager(show_callback=self.show_window, quit_callback=self.quit_app)
            self.tray.start()
        else:
            self.tray = None

        self.geometry("900x600")
        self.minsize(800, 500)
        
        # Set application and window icon (override CustomTkinter default icon)
        icon_path = resource_path('icon.ico')
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
        # Prevent CustomTkinter from resetting to the blue C icon at 200ms
        self._windows_set_titlebar_icon = lambda: self.iconbitmap(icon_path) if os.path.exists(icon_path) else None
        self.after(250, lambda: self.iconbitmap(icon_path) if os.path.exists(icon_path) else None)
        self.after(500, lambda: self.iconbitmap(icon_path) if os.path.exists(icon_path) else None)
            
        # Window protocol: Portable closes completely; Installed minimizes to tray
        if is_portable():
            self.protocol("WM_DELETE_WINDOW", self.quit_app)
        else:
            self.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # State
        self.thumbnail_images = {}
        self.selected_video = None
        self.current_results = []
        self._search_after_id = None
        self._search_generation = 0
        
        # Managers
        self.download_manager = DownloadManager(download_fn=download_video)
        self.download_manager.on_queue_update = self._on_queue_update
        self.download_manager.on_job_complete = self._on_job_complete
        self.download_manager.on_job_error = self._on_job_error
        
        # --- Custom Tab Bar ---
        self.tab_bar = ctk.CTkFrame(self, height=40, fg_color="transparent")
        self.tab_bar.pack(fill="x", padx=10, pady=(10, 0))
        
        self.btn_tab_main = ctk.CTkButton(self.tab_bar, text=t('app_title'), command=lambda: self.select_tab("main"))
        self.btn_tab_main.pack(side="left", padx=5)
        
        self.btn_tab_history = ctk.CTkButton(self.tab_bar, text=t('history'), command=lambda: self.select_tab("history"))
        self.btn_tab_history.pack(side="left", padx=5)
        
        self.btn_tab_settings = ctk.CTkButton(self.tab_bar, text=t('theme'), command=lambda: self.select_tab("settings"))
        self.btn_tab_settings.pack(side="left", padx=5)
        
        # Tab Containers
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=10, pady=10)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        
        self.tab_main = ctk.CTkFrame(self.container, fg_color="transparent")
        self.tab_history = ctk.CTkFrame(self.container, fg_color="transparent")
        self.tab_settings = ctk.CTkFrame(self.container, fg_color="transparent")
        
        # Build Tabs
        self.build_main_tab()
        self.build_history_tab()
        self.build_settings_tab()
        
        self.select_tab("main")
        
        # Drag and Drop
        try:
            windnd.hook_dropfiles(self.winfo_id(), func=self.on_drop)
        except Exception as e:
            print(f"Drag and drop not supported: {e}")
            
        # Initial updates
        self.update_language_ui()

    def get_active_browser(self):
        """Return browser name if cookies are enabled, otherwise None"""
        if self.config.get('use_cookies'):
            return self.config.get('cookies_browser', 'Chrome')
        return None
        
    def select_tab(self, name):
        active_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        inactive_color = "transparent"
        text_color_active = ctk.ThemeManager.theme["CTkButton"]["text_color"]
        text_color_inactive = "gray60"
        
        self.btn_tab_main.configure(fg_color=inactive_color, text_color=text_color_inactive)
        self.btn_tab_history.configure(fg_color=inactive_color, text_color=text_color_inactive)
        self.btn_tab_settings.configure(fg_color=inactive_color, text_color=text_color_inactive)
        
        self.tab_main.grid_forget()
        self.tab_history.grid_forget()
        self.tab_settings.grid_forget()
        
        if name == "main":
            self.btn_tab_main.configure(fg_color=active_color, text_color=text_color_active)
            self.tab_main.grid(row=0, column=0, sticky="nsew")
        elif name == "history":
            self.btn_tab_history.configure(fg_color=active_color, text_color=text_color_active)
            self.tab_history.grid(row=0, column=0, sticky="nsew")
        elif name == "settings":
            self.btn_tab_settings.configure(fg_color=active_color, text_color=text_color_active)
            self.tab_settings.grid(row=0, column=0, sticky="nsew")
        
    def build_main_tab(self):
        self.tab_main.grid_columnconfigure(0, weight=1)
        self.tab_main.grid_rowconfigure(1, weight=1) # Results area
        
        # 1. Search Bar
        self.search_frame = ctk.CTkFrame(self.tab_main)
        self.search_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.search_frame.grid_columnconfigure(0, weight=1)
        
        self.entry_search = ctk.CTkEntry(self.search_frame, height=38, font=("Segoe UI", 14))
        self.entry_search.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.entry_search.bind("<Return>", lambda e: self.trigger_search())
        self.entry_search.bind("<KeyRelease>", self.on_search_keyrelease)
        
        self.btn_search = ctk.CTkButton(self.search_frame, width=100)
        self.btn_search.grid(row=0, column=1, padx=10, pady=10)
        self.btn_search.configure(command=self.trigger_search)
        
        # 2. Results Area
        self.split_frame = ctk.CTkFrame(self.tab_main, fg_color="transparent")
        self.split_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.split_frame.grid_columnconfigure(0, weight=6)
        self.split_frame.grid_columnconfigure(1, weight=4)
        self.split_frame.grid_rowconfigure(0, weight=1)
        
        self.results_frame = ctk.CTkScrollableFrame(self.split_frame)
        self.results_frame.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        self.result_widgets = []
        
        self.right_container = ctk.CTkFrame(self.split_frame, fg_color="transparent")
        self.right_container.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        self.right_container.grid_columnconfigure(0, weight=1)
        self.right_container.grid_rowconfigure(0, weight=1)
        
        self.right_scroll = ctk.CTkScrollableFrame(self.right_container, fg_color="transparent")
        self.right_scroll.grid(row=0, column=0, sticky="nsew")
        self.right_scroll.grid_columnconfigure(0, weight=1)
        
        self.details_panel = DetailsPanel(self.right_scroll)
        self.details_panel.pack(fill="x", pady=(0, 10))
        
        self.trim_frame = ctk.CTkFrame(self.right_scroll)
        self.trim_frame.pack(fill="x", pady=10)
        self.lbl_trim = ctk.CTkLabel(self.trim_frame, text="")
        self.lbl_trim.pack(anchor="w", padx=10, pady=(5,0))
        self.chk_trim = ctk.CTkCheckBox(self.trim_frame, text="", command=self.toggle_trim)
        self.chk_trim.pack(anchor="e", padx=10)
        self.range_slider = RangeSlider(self.trim_frame)
        self.range_slider.pack(fill="x", padx=10, pady=10)
        self.chk_trim.deselect()
        
        self.options_frame = ctk.CTkFrame(self.right_scroll)
        self.options_frame.pack(fill="x", pady=10)
        self.options_frame.grid_columnconfigure(1, weight=1)
        
        self.lbl_format = ctk.CTkLabel(self.options_frame, text="")
        self.lbl_format.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.combo_format = ctk.CTkComboBox(self.options_frame, values=["Video (MP4)", "Audio (MP3)"], command=self.update_estimate)
        self.combo_format.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        self.lbl_quality = ctk.CTkLabel(self.options_frame, text="")
        self.lbl_quality.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.combo_quality = ctk.CTkComboBox(self.options_frame, values=["Auto", "4K", "1080p", "720p", "480p", "360p"], command=self.update_estimate)
        self.combo_quality.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Download Folder selector
        self.lbl_folder_main = ctk.CTkLabel(self.options_frame, text="")
        self.lbl_folder_main.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        self.frame_folder = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.frame_folder.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.frame_folder.grid_columnconfigure(0, weight=1)
        
        self.lbl_current_folder = ctk.CTkLabel(self.frame_folder, text=self.config['download_path'], text_color="gray75", anchor="w")
        self.lbl_current_folder.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        
        self.btn_change_folder = ctk.CTkButton(self.frame_folder, text="📁", width=36, fg_color="#495057", hover_color="#343a40", command=self.choose_folder)
        self.btn_change_folder.grid(row=0, column=1, sticky="e")
        
        self.lbl_size = ctk.CTkLabel(self.options_frame, text="", text_color="gray60")
        self.lbl_size.grid(row=3, column=0, columnspan=2, padx=10, pady=5)
        
        self.action_frame = ctk.CTkFrame(self.right_container, fg_color="transparent")
        self.action_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.action_frame.grid_columnconfigure((0,1), weight=1)
        
        self.btn_download = ctk.CTkButton(self.action_frame, fg_color="#28a745", hover_color="#218838", command=self.add_download)
        self.btn_download.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.btn_queue = ctk.CTkButton(self.action_frame, fg_color="#17a2b8", hover_color="#138496", command=self.add_queue)
        self.btn_queue.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        self.lbl_status = ctk.CTkLabel(self.tab_main, text="", text_color="gray60")
        self.lbl_status.grid(row=2, column=0, pady=5)
        
        self.queue_panel = QueuePanel(self.tab_main)
        self.queue_panel.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        self.queue_panel.btn_clear.configure(command=self.clear_queue)

    def build_history_tab(self):
        self.tab_history.grid_columnconfigure(0, weight=1)
        self.tab_history.grid_rowconfigure(1, weight=1)
        
        btn_frame = ctk.CTkFrame(self.tab_history, fg_color="transparent")
        btn_frame.grid(row=0, column=0, sticky="ew")
        
        self.btn_clear_hist = ctk.CTkButton(btn_frame, command=self.clear_history)
        self.btn_clear_hist.pack(side="right", padx=10, pady=10)
        
        self.hist_scroll = ctk.CTkScrollableFrame(self.tab_history)
        self.hist_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.hist_widgets = []
        
        self.refresh_history()
        
    def build_settings_tab(self):
        self.tab_settings.grid_columnconfigure((0,1), weight=1)
        
        # Language
        self.lbl_lang = ctk.CTkLabel(self.tab_settings)
        self.lbl_lang.grid(row=0, column=0, padx=20, pady=20, sticky="e")
        self.combo_lang = ctk.CTkComboBox(self.tab_settings, values=["English", "Español"], command=self.change_language)
        self.combo_lang.grid(row=0, column=1, padx=20, pady=20, sticky="w")
        self.combo_lang.set("English" if self.config['language'] == 'en' else "Español")
        
        # Theme
        self.lbl_theme = ctk.CTkLabel(self.tab_settings)
        self.lbl_theme.grid(row=1, column=0, padx=20, pady=20, sticky="e")
        self.switch_theme = ctk.CTkSwitch(self.tab_settings, text="Dark Mode", command=self.toggle_theme)
        self.switch_theme.grid(row=1, column=1, padx=20, pady=20, sticky="w")
        if self.config['theme'] == 'dark':
            self.switch_theme.select()
            
        # Folder
        self.lbl_folder = ctk.CTkLabel(self.tab_settings)
        self.lbl_folder.grid(row=2, column=0, padx=20, pady=20, sticky="e")
        self.btn_folder = ctk.CTkButton(self.tab_settings, command=self.choose_folder)
        self.btn_folder.grid(row=2, column=1, padx=20, pady=20, sticky="w")
        self.lbl_folder_val = ctk.CTkLabel(self.tab_settings, text=self.config['download_path'], text_color="gray60")
        self.lbl_folder_val.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Cookies Settings
        self.chk_cookies = ctk.CTkCheckBox(self.tab_settings, text="", command=self.toggle_cookies)
        self.chk_cookies.grid(row=4, column=0, padx=20, pady=20, sticky="e")
        if self.config.get('use_cookies'):
            self.chk_cookies.select()
            
        self.combo_browser = ctk.CTkComboBox(self.tab_settings, values=["Chrome", "Edge", "Firefox", "Brave", "Opera", "Vivaldi"], command=self.change_browser)
        self.combo_browser.grid(row=4, column=1, padx=20, pady=20, sticky="w")
        self.combo_browser.set(self.config.get('cookies_browser', 'Chrome'))

    def update_language_ui(self):
        """Update all text based on current language."""
        self.btn_tab_main.configure(text=t('app_title'))
        self.btn_tab_history.configure(text=t('history'))
        self.btn_tab_settings.configure(text=t('theme'))
        
        self.entry_search.configure(placeholder_text=t('search_placeholder'))
        self.btn_search.configure(text=t('search_btn'))
        
        self.lbl_trim.configure(text=t('trim_label'))
        self.chk_trim.configure(text=t('enable_trim'))
        
        self.lbl_format.configure(text=t('format'))
        self.combo_format.configure(values=[t('video_mp4'), t('audio_mp3')])
        
        self.lbl_quality.configure(text=t('quality'))
        
        self.btn_download.configure(text=t('download'))
        self.btn_queue.configure(text=t('add_to_queue'))
        
        self.lbl_status.configure(text=t('ready'))
        
        self.details_panel.update_language()
        self.queue_panel.update_language()
        
        self.btn_clear_hist.configure(text=t('clear_history'))
        
        self.lbl_lang.configure(text=t('language'))
        self.lbl_theme.configure(text=t('theme'))
        self.lbl_folder.configure(text=t('folder'))
        self.btn_folder.configure(text=t('folder'))
        if hasattr(self, 'lbl_folder_main'):
            self.lbl_folder_main.configure(text=t('folder'))
        if hasattr(self, 'lbl_current_folder'):
            self.lbl_current_folder.configure(text=self.config.get('download_path', ''))
        
        self.chk_cookies.configure(text=t('use_cookies'))
        
        self.refresh_history()

    def change_language(self, choice):
        lang = 'en' if choice == 'English' else 'es'
        self.config['language'] = lang
        set_language(lang)
        save_config(self.config)
        self.update_language_ui()

    def toggle_theme(self):
        mode = "dark" if self.switch_theme.get() else "light"
        self.config['theme'] = mode
        ctk.set_appearance_mode(mode)
        save_config(self.config)
        self.range_slider.refresh_theme()
        
    def choose_folder(self):
        initial = self.config.get('download_path', os.path.expanduser("~\\Downloads"))
        path = filedialog.askdirectory(initialdir=initial)
        if path:
            self.config['download_path'] = path
            save_config(self.config)
            if hasattr(self, 'lbl_folder_val'):
                self.lbl_folder_val.configure(text=path)
            if hasattr(self, 'lbl_current_folder'):
                self.lbl_current_folder.configure(text=path)
            
    def toggle_cookies(self):
        self.config['use_cookies'] = self.chk_cookies.get() == 1
        save_config(self.config)
        
    def change_browser(self, choice):
        self.config['cookies_browser'] = choice
        save_config(self.config)

    # --- Search Logic ---
    def on_search_keyrelease(self, event):
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
            self._search_after_id = None
            
        query = self.entry_search.get().strip()
        if not query:
            self.clear_results()
            return
            
        if query.startswith("http") or "youtu" in query:
            return
            
        self._search_after_id = self.after(500, self.do_search, query)

    def trigger_search(self):
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
            self._search_after_id = None
        query = self.entry_search.get().strip()
        if query:
            self.do_search(query)
            
    def do_search(self, query):
        if len(query) < 3 and not query.startswith("http"):
            return
            
        self._search_generation += 1
        gen = self._search_generation
        
        self.lbl_status.configure(text=t('searching'))
        self.btn_search.configure(state="disabled")
        
        b_cookies = self.get_active_browser()
        
        if is_playlist_url(query):
            threading.Thread(target=self._search_playlist_thread, args=(query, gen, b_cookies), daemon=True).start()
        else:
            threading.Thread(target=self._search_thread, args=(query, gen, b_cookies), daemon=True).start()

    def _search_thread(self, query, gen, b_cookies):
        results = search_videos(query, max_results=10, cookies_browser=b_cookies)
        if gen == self._search_generation:
            self.after(0, self.show_results, results)
            
    def _search_playlist_thread(self, query, gen, b_cookies):
        results = get_playlist_videos(query, cookies_browser=b_cookies)
        if gen == self._search_generation:
            self.after(0, self.show_results, results, True)

    def clear_results(self):
        for w in self.result_widgets:
            w.destroy()
        self.result_widgets.clear()
        self.current_results.clear()
        self.selected_video = None
        self.thumbnail_images.clear()
        self.details_panel.clear()
        self.lbl_size.configure(text="")

    def show_results(self, results, is_playlist=False):
        self.btn_search.configure(state="normal")
        self.clear_results()
        self.current_results = results
        
        if not results:
            self.lbl_status.configure(text=t('no_results'))
            return
            
        if is_playlist:
            self.lbl_status.configure(text=t('playlist_detected', count=len(results)))
            btn_dl_all = ctk.CTkButton(self.results_frame, text=t('download_all'), fg_color="#28a745", command=self.download_all)
            btn_dl_all.pack(pady=5, fill="x")
            self.result_widgets.append(btn_dl_all)
        else:
            self.lbl_status.configure(text=t('results_found', n=len(results)))

        for idx, video in enumerate(results):
            frame = ctk.CTkFrame(self.results_frame, corner_radius=8)
            frame.pack(fill="x", pady=4, padx=5)
            frame.grid_columnconfigure(1, weight=1)
            self.result_widgets.append(frame)
            
            thumb_lbl = ctk.CTkLabel(frame, text="", width=120, height=68)
            thumb_lbl.grid(row=0, column=0, padx=8, pady=8, rowspan=2)
            if video.get('thumbnail'):
                self.load_thumbnail(video['thumbnail'], thumb_lbl, idx)
                
            lbl_title = ctk.CTkLabel(frame, text=video['title'], font=("Segoe UI", 12, "bold"), anchor="w", wraplength=350, justify="left")
            lbl_title.grid(row=0, column=1, padx=5, pady=(8,0), sticky="w")
            
            lbl_dur = ctk.CTkLabel(frame, text=video['duration_str'], font=("Segoe UI", 11), text_color="gray60")
            lbl_dur.grid(row=1, column=1, padx=5, pady=(0,8), sticky="w")
            
            btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
            btn_frame.grid(row=0, column=2, rowspan=2, padx=5, pady=5)
            
            ctk.CTkButton(btn_frame, text=t('preview'), width=60, command=lambda v=video: webbrowser.open(v['url'])).pack(pady=2)
            ctk.CTkButton(btn_frame, text=t('select'), width=60, command=lambda v=video, f=frame: self.select_video(v, f)).pack(pady=2)

    def load_thumbnail(self, url, label, idx):
        def _fetch():
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    img = Image.open(io.BytesIO(resp.content)).resize((120, 68), Image.LANCZOS)
                    ctk_img = ctk.CTkImage(img, size=(120, 68))
                    self.thumbnail_images[idx] = ctk_img
                    self.after(0, lambda: label.configure(image=ctk_img))
            except Exception:
                pass
        threading.Thread(target=_fetch, daemon=True).start()

    def select_video(self, video, frame):
        self.selected_video = video
        for w in self.result_widgets:
            if isinstance(w, ctk.CTkFrame):
                w.configure(fg_color=("gray86", "gray17"))
        frame.configure(fg_color=("gray70", "#1a3a5c"))
        
        self.lbl_status.configure(text=t('selected', title=video['title'][:40]+"..."))
        
        if video.get('duration'):
            self.range_slider.set_duration(video['duration'])
            
        self.details_panel.clear()
        
        b_cookies = self.get_active_browser()
        
        def _fetch_details():
            try:
                from backend import get_full_video_info
                info = get_full_video_info(video['url'], cookies_browser=b_cookies)
                self.after(0, lambda: self.details_panel.set_info(info))
                self.after(0, self.update_estimate)
            except Exception as e:
                print(f"Warning: Could not fetch video details. {e}")
            
        threading.Thread(target=_fetch_details, daemon=True).start()
        
    def toggle_trim(self):
        if self.chk_trim.get():
            self.range_slider.configure(fg_color=("gray78", "gray20"))
        else:
            self.range_slider.configure(fg_color=("gray85", "gray25"))
            
    def update_estimate(self, *_):
        if not self.selected_video:
            return
        format_val = 'mp3' if 'MP3' in self.combo_format.get() else 'mp4'
        quality = self.combo_quality.get()
        
        if format_val == 'mp3':
            self.combo_quality.configure(state="disabled")
        else:
            self.combo_quality.configure(state="normal")
            
        self.lbl_size.configure(text=t('searching'))
        b_cookies = self.get_active_browser()
        
        def _est():
            try:
                size = estimate_file_size(self.selected_video['url'], format_val, quality, cookies_browser=b_cookies)
                self.after(0, lambda: self.lbl_size.configure(text=t('estimated_size', size=size)))
            except Exception as e:
                print(f"Warning: Could not estimate file size. {e}")
                self.after(0, lambda: self.lbl_size.configure(text=t('estimated_size', size="Unknown")))
        threading.Thread(target=_est, daemon=True).start()

    # --- Download ---
    def get_download_params(self, video):
        format_val = 'mp3' if 'MP3' in self.combo_format.get() else 'mp4'
        quality = self.combo_quality.get()
        
        start_time, end_time = None, None
        if self.chk_trim.get() and video.get('duration'):
            s, e = self.range_slider.get_range()
            if s > 0.5: start_time = s
            if e < video['duration'] - 0.5: end_time = e
            
        return format_val, quality, start_time, end_time

    def add_download(self):
        if not self.selected_video:
            messagebox.showwarning(t('warning'), t('select_video_first'))
            return
        fmt, q, st, et = self.get_download_params(self.selected_video)
        b_cookies = self.get_active_browser()
        job = DownloadJob(self.selected_video, fmt, q, st, et, self.config['download_path'], cookies_browser=b_cookies)
        self.download_manager.add_job(job)
        
    def add_queue(self):
        self.add_download()
        
    def download_all(self):
        fmt, q, st, et = 'mp4', 'Auto', None, None
        b_cookies = self.get_active_browser()
        for video in self.current_results:
            job = DownloadJob(video, fmt, q, st, et, self.config['download_path'], cookies_browser=b_cookies)
            self.download_manager.add_job(job)
            
    # --- Queue Callbacks ---
    def _on_queue_update(self):
        self.after(0, lambda: self.queue_panel.update_jobs(self.download_manager.get_all_jobs()))
        
    def _on_job_complete(self, job):
        if self.tray:
            self.after(0, lambda: self.tray.notify(t('success'), t('tray_download_done', title=job.title)))
        final_path = getattr(job, 'file_path', job.output_path)
        add_entry(job.title, job.video['url'], final_path, job.format_type, job.quality)
        self.after(0, self.refresh_history)
        
    def _on_job_error(self, job, err):
        if self.tray:
            self.after(0, lambda: self.tray.notify(t('error'), t('download_error')))
        print(f"Error downloading {job.title}: {err}")
        
    def clear_queue(self):
        self.download_manager.clear_completed()
        self._on_queue_update()

    # --- History ---
    def refresh_history(self):
        for w in self.hist_widgets:
            w.destroy()
        self.hist_widgets.clear()
        
        history = get_history()
        if not history:
            lbl = ctk.CTkLabel(self.hist_scroll, text=t('no_history'), text_color="gray60")
            lbl.pack(pady=20)
            self.hist_widgets.append(lbl)
            return
            
        for idx, entry in enumerate(history):
            f = ctk.CTkFrame(self.hist_scroll)
            f.pack(fill="x", pady=4, padx=5)
            self.hist_widgets.append(f)
            
            f.grid_columnconfigure(0, weight=1)
            
            p = entry.get('file_path', '')
            folder = p if os.path.isdir(p) else os.path.dirname(p)
            
            ctk.CTkLabel(f, text=entry['title'], font=("Segoe UI", 12, "bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=(5,0))
            ctk.CTkLabel(f, text=f"{entry['date']} • {entry['format'].upper()} • {entry['quality']}", font=("Segoe UI", 10), text_color="gray60", anchor="w").grid(row=1, column=0, sticky="w", padx=10, pady=(0,2))
            ctk.CTkLabel(f, text=f"📁 {p}", font=("Segoe UI", 9), text_color="gray50", anchor="w").grid(row=2, column=0, sticky="w", padx=10, pady=(0,5))
            
            # Action Buttons
            btn_box = ctk.CTkFrame(f, fg_color="transparent")
            btn_box.grid(row=0, column=1, rowspan=3, padx=5, pady=5)
            
            if p and os.path.isfile(p):
                btn_open = ctk.CTkButton(btn_box, text=t('open_file'), width=65, fg_color="#28a745", hover_color="#218838", command=lambda path=p: os.startfile(path))
                btn_open.pack(side="left", padx=2)

            btn_folder = ctk.CTkButton(btn_box, text=t('open_folder'), width=85, fg_color="#17a2b8", hover_color="#138496", command=lambda fp=folder: os.startfile(fp) if os.path.exists(fp) else None)
            btn_folder.pack(side="left", padx=2)
            
            btn_remove = ctk.CTkButton(btn_box, text=t('remove_entry'), width=65, fg_color="#6c757d", hover_color="#5a6268", command=lambda i=idx: self.remove_history_entry(i))
            btn_remove.pack(side="left", padx=2)
            
            if p and os.path.isfile(p):
                btn_delete = ctk.CTkButton(btn_box, text=t('delete_file'), width=65, fg_color="#dc3545", hover_color="#c82333", command=lambda i=idx, path=p: self.delete_history_file(i, path))
                btn_delete.pack(side="left", padx=2)

    def remove_history_entry(self, index):
        from history import remove_entry
        remove_entry(index)
        self.refresh_history()

    def delete_history_file(self, index, file_path):
        if messagebox.askyesno(t('warning'), t('confirm_delete')):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Could not delete file: {e}")
            from history import remove_entry
            remove_entry(index)
            self.refresh_history()

    def clear_history(self):
        clear_history()
        self.refresh_history()
        
    # --- Drag and Drop ---
    def on_drop(self, files):
        if not files: return
        try:
            text = files[0].decode('utf-8')
            if "youtube.com" in text or "youtu.be" in text:
                self.entry_search.delete(0, 'end')
                self.entry_search.insert(0, text)
                self.trigger_search()
        except:
            pass

    # --- App Lifecycle ---
    def hide_window(self):
        self.withdraw()
        
    def show_window(self):
        self.after(0, self.deiconify)
        
    def quit_app(self):
        if self.tray:
            try:
                self.tray.stop()
            except Exception:
                pass
        try:
            self.destroy()
        except Exception:
            pass
        os._exit(0)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
