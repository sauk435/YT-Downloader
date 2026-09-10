# ui_widgets.py — Custom widgets for YouTube Downloader

import customtkinter as ctk
import tkinter as tk
from i18n import t


# ──────────────────────────────────────────────────────────
#  RangeSlider (Trim Handle)
# ──────────────────────────────────────────────────────────
class RangeSlider(ctk.CTkFrame):
    """Dual-handle slider for selecting a time range."""

    def __init__(self, master, total_duration=100, on_change=None, **kwargs):
        super().__init__(master, **kwargs)
        self.total_duration = max(total_duration, 1)
        self.on_change = on_change
        self.start_val = 0
        self.end_val = self.total_duration

        self.grid_columnconfigure(1, weight=1)

        self.lbl_start = ctk.CTkLabel(self, text="00:00", width=60, font=("Consolas", 12))
        self.lbl_start.grid(row=0, column=0, padx=(5, 2))

        self.canvas = tk.Canvas(self, height=50, bg="#2b2b2b", highlightthickness=0, cursor="hand2")
        self.canvas.grid(row=0, column=1, sticky="ew", padx=2, pady=5)

        self.lbl_end = ctk.CTkLabel(self, text="00:00", width=60, font=("Consolas", 12))
        self.lbl_end.grid(row=0, column=2, padx=(2, 5))

        self.lbl_total = ctk.CTkLabel(self, text="/ 00:00", width=60, font=("Consolas", 10),
                                      text_color="gray60")
        self.lbl_total.grid(row=0, column=3, padx=(0, 5))

        self._dragging = None
        self._handle_radius = 8
        self._bar_y = 25
        self._bar_height = 8

        self.canvas.bind("<Configure>", self._draw_slider)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self._update_labels()

    def refresh_theme(self):
        self._draw_slider()

    def set_duration(self, duration):
        self.total_duration = max(duration, 1)
        self.start_val = 0
        self.end_val = self.total_duration
        self._update_labels()
        self._draw_slider()

    def get_range(self):
        return (self.start_val, self.end_val)

    def _val_to_x(self, val):
        w = self.canvas.winfo_width()
        margin = self._handle_radius + 4
        usable = w - 2 * margin
        return margin + (val / self.total_duration) * usable

    def _x_to_val(self, x):
        w = self.canvas.winfo_width()
        margin = self._handle_radius + 4
        usable = w - 2 * margin
        val = ((x - margin) / usable) * self.total_duration
        return max(0, min(self.total_duration, val))

    def _draw_slider(self, event=None):
        mode = ctk.get_appearance_mode()
        bg_color = "#2b2b2b" if mode == "Dark" else "#ebebeb"
        self.canvas.configure(bg=bg_color)
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        y, h, r = self._bar_y, self._bar_height, self._handle_radius

        self.canvas.create_rectangle(
            self._val_to_x(0), y - h // 2,
            self._val_to_x(self.total_duration), y + h // 2,
            fill="#555555", outline=""
        )
        x_start = self._val_to_x(self.start_val)
        x_end = self._val_to_x(self.end_val)
        self.canvas.create_rectangle(x_start, y - h // 2, x_end, y + h // 2,
                                     fill="#1f9eff", outline="")
        self.canvas.create_oval(x_start - r, y - r, x_start + r, y + r,
                                fill="#00cc66", outline="#00ff80", width=2)
        self.canvas.create_oval(x_end - r, y - r, x_end + r, y + r,
                                fill="#cc3333", outline="#ff5555", width=2)

    def _on_press(self, event):
        x_s = self._val_to_x(self.start_val)
        x_e = self._val_to_x(self.end_val)
        r = self._handle_radius + 4
        ds, de = abs(event.x - x_s), abs(event.x - x_e)
        if ds <= r and ds <= de:
            self._dragging = 'start'
        elif de <= r:
            self._dragging = 'end'
        else:
            self._dragging = 'start' if ds < de else 'end'
            self._on_drag(event)

    def _on_drag(self, event):
        if not self._dragging:
            return
        val = self._x_to_val(event.x)
        if self._dragging == 'start':
            self.start_val = max(0, min(val, self.end_val - 1))
        else:
            self.end_val = min(self.total_duration, max(val, self.start_val + 1))
        self._update_labels()
        self._draw_slider()
        if self.on_change:
            self.on_change(self.start_val, self.end_val)

    def _on_release(self, event):
        self._dragging = None

    def _update_labels(self):
        self.lbl_start.configure(text=self._fmt(self.start_val))
        self.lbl_end.configure(text=self._fmt(self.end_val))
        self.lbl_total.configure(text=f"/ {self._fmt(self.total_duration)}")

    @staticmethod
    def _fmt(seconds):
        s = int(seconds)
        mins, secs = divmod(s, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02}:{mins:02}:{secs:02}" if hours > 0 else f"{mins:02}:{secs:02}"


# ──────────────────────────────────────────────────────────
#  DetailsPanel — Video info panel
# ──────────────────────────────────────────────────────────
class DetailsPanel(ctk.CTkFrame):
    """Expandable panel showing detailed video information."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._expanded = False

        self.toggle_btn = ctk.CTkButton(
            self, text=t('show_details'), width=120, height=28,
            fg_color="transparent", text_color="gray60",
            hover_color=("gray80", "gray30"),
            command=self.toggle
        )
        self.toggle_btn.grid(row=0, column=0, padx=5, pady=2, sticky="w")

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid_columnconfigure(1, weight=1)
        # Initially hidden
        self._info_labels = {}

        rows = [('channel', t('channel')), ('views', t('views')),
                ('upload_date', t('upload_date')), ('likes', t('likes'))]
        for i, (key, label) in enumerate(rows):
            lbl = ctk.CTkLabel(self.content, text=f"{label}:", font=("Segoe UI", 11, "bold"),
                               anchor="w", width=100)
            lbl.grid(row=i, column=0, padx=(10, 5), pady=1, sticky="w")
            val = ctk.CTkLabel(self.content, text="—", font=("Segoe UI", 11),
                               anchor="w", text_color="gray60")
            val.grid(row=i, column=1, padx=5, pady=1, sticky="w")
            self._info_labels[key] = val

        # Description
        r = len(rows)
        lbl_d = ctk.CTkLabel(self.content, text=f"{t('description')}:",
                             font=("Segoe UI", 11, "bold"), anchor="nw", width=100)
        lbl_d.grid(row=r, column=0, padx=(10, 5), pady=1, sticky="nw")
        self._desc_label = ctk.CTkLabel(
            self.content, text="—", font=("Segoe UI", 10),
            anchor="nw", text_color="gray60", wraplength=500, justify="left"
        )
        self._desc_label.grid(row=r, column=1, padx=5, pady=1, sticky="w")

    def toggle(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.content.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
            self.toggle_btn.configure(text=t('hide_details'))
        else:
            self.content.grid_forget()
            self.toggle_btn.configure(text=t('show_details'))

    def set_info(self, info):
        """Update displayed info. info is a dict from get_full_video_info()."""
        for key in ('channel', 'views', 'upload_date', 'likes'):
            if key in self._info_labels and key in info:
                self._info_labels[key].configure(text=str(info[key]))
        desc = info.get('description', '—')
        if len(desc) > 300:
            desc = desc[:300] + "..."
        self._desc_label.configure(text=desc or "—")

    def clear(self):
        for lbl in self._info_labels.values():
            lbl.configure(text="—")
        self._desc_label.configure(text="—")

    def update_language(self):
        """Refresh labels when language changes."""
        self.toggle_btn.configure(
            text=t('hide_details') if self._expanded else t('show_details')
        )


# ──────────────────────────────────────────────────────────
#  QueuePanel — Download queue display
# ──────────────────────────────────────────────────────────
class QueuePanel(ctk.CTkFrame):
    """Panel showing the download queue status."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._expanded = True

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        header.grid_columnconfigure(1, weight=1)
        
        self.btn_toggle = ctk.CTkButton(header, text="▼", width=30, height=26, fg_color="transparent", command=self.toggle)
        self.btn_toggle.grid(row=0, column=0, padx=(5,0))

        self.lbl_title = ctk.CTkLabel(header, text=t('queue_title'),
                                      font=("Segoe UI", 12, "bold"), anchor="w")
        self.lbl_title.grid(row=0, column=1, sticky="w", padx=5)

        self.btn_clear = ctk.CTkButton(
            header, text=t('clear_queue'), width=120, height=26,
            fg_color="transparent", text_color="gray60",
            hover_color=("gray80", "gray30"),
        )
        self.btn_clear.grid(row=0, column=2, padx=5)

        self.items_frame = ctk.CTkScrollableFrame(self, height=120)
        self.items_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        self.items_frame.grid_columnconfigure(0, weight=1)

        self._item_widgets = []

    def toggle(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.items_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
            self.btn_toggle.configure(text="▼")
        else:
            self.items_frame.grid_forget()
            self.btn_toggle.configure(text="▶")

    def update_jobs(self, jobs):
        """Refresh the queue display with current jobs."""
        for w in self._item_widgets:
            w.destroy()
        self._item_widgets.clear()

        if not jobs:
            lbl = ctk.CTkLabel(self.items_frame, text=t('queue_empty'),
                               text_color="gray60")
            lbl.pack(pady=5)
            self._item_widgets.append(lbl)
            return

        for job in jobs:
            frame = ctk.CTkFrame(self.items_frame, corner_radius=6, height=36)
            frame.pack(fill="x", pady=2, padx=2)
            frame.grid_columnconfigure(0, weight=1)
            self._item_widgets.append(frame)

            title = job.title
            if len(title) > 50:
                title = title[:50] + "..."
            lbl_title = ctk.CTkLabel(frame, text=title, font=("Segoe UI", 11),
                                     anchor="w")
            lbl_title.grid(row=0, column=0, padx=8, pady=4, sticky="w")

            status_text, color = self._status_display(job)
            lbl_status = ctk.CTkLabel(frame, text=status_text,
                                      font=("Segoe UI", 11), text_color=color)
            lbl_status.grid(row=0, column=1, padx=8, pady=4, sticky="e")

    @staticmethod
    def _status_display(job):
        if job.status == 'downloading':
            speed = f" ({job.speed})" if job.speed else ""
            return f"{job.progress:.0f}%{speed}", "#f39c12"
        elif job.status == 'completed':
            return t('completed'), "#28a745"
        elif job.status == 'failed':
            return t('failed'), "#e74c3c"
        else:
            return t('waiting'), "gray60"

    def update_language(self):
        self.lbl_title.configure(text=t('queue_title'))
        self.btn_clear.configure(text=t('clear_queue'))
