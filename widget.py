import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
import pystray
from PIL import Image, ImageDraw
import data_fetcher

class UsageWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AGY Monitor")
        
        # UI Styling (Dark mode flat design)
        self.bg_color = "#1E1E1E"
        self.fg_color = "#E0E0E0"
        self.accent_color = "#4FC3F7"
        self.warning_color = "#FF5252"
        
        self.root.configure(bg=self.bg_color)
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True) # Borderless window
        self.root.withdraw() # Hide initially
        
        # Set window size
        self.width = 280
        self.base_height = 140
        self.expanded_height = 280
        self.root.geometry(f"{self.width}x{self.base_height}")
        
        self.build_ui()
        self.setup_tray()
        
        # State
        self.show_details = tk.BooleanVar(value=False)
        self.is_fetching = False
        
        # Start update loop (3 minutes = 180 seconds)
        self.update_thread = threading.Thread(target=self.auto_update_loop, daemon=True)
        self.update_thread.start()

    def build_ui(self):
        # Main Frame
        self.main_frame = tk.Frame(self.root, bg=self.bg_color, highlightbackground="#333333", highlightthickness=1)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header (Draggable)
        self.header = tk.Frame(self.main_frame, bg="#2D2D2D", height=30)
        self.header.pack(fill=tk.X)
        self.header.bind("<ButtonPress-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)
        
        title = tk.Label(self.header, text="AGY Model Monitor", bg="#2D2D2D", fg=self.fg_color, font=("Segoe UI", 9, "bold"))
        title.pack(side=tk.LEFT, padx=10, pady=5)
        title.bind("<ButtonPress-1>", self.start_move)
        title.bind("<B1-Motion>", self.do_move)
        
        close_btn = tk.Label(self.header, text="X", bg="#2D2D2D", fg="#888888", font=("Segoe UI", 9, "bold"), cursor="hand2")
        close_btn.pack(side=tk.RIGHT, padx=10)
        close_btn.bind("<Button-1>", lambda e: self.hide_window())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="white"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#888888"))
        
        # Content Frame
        self.content = tk.Frame(self.main_frame, bg=self.bg_color, padx=15, pady=10)
        self.content.pack(fill=tk.BOTH, expand=True)
        
        # Gemini 5hr (Primary)
        tk.Label(self.content, text="Gemini (5 小時用量)", bg=self.bg_color, fg="#AAAAAA", font=("Segoe UI", 9)).pack(anchor="w")
        
        self.gemini_pct_lbl = tk.Label(self.content, text="--%", bg=self.bg_color, fg=self.accent_color, font=("Segoe UI", 24, "bold"))
        self.gemini_pct_lbl.pack(anchor="w", pady=(0, 2))
        
        self.gemini_text_lbl = tk.Label(self.content, text="-- / --", bg=self.bg_color, fg=self.fg_color, font=("Segoe UI", 10))
        self.gemini_text_lbl.pack(anchor="w")
        
        # Details checkbutton
        self.cb_details = tk.Checkbutton(self.content, text="顯示詳細資訊 (外部模型/每週)", bg=self.bg_color, fg="#888888", 
                                         selectcolor=self.bg_color, activebackground=self.bg_color, activeforeground="white",
                                         command=self.toggle_details, font=("Segoe UI", 8))
        self.cb_details.pack(anchor="w", pady=(10, 0))
        
        # Expanded Frame (Hidden initially)
        self.expanded_frame = tk.Frame(self.content, bg=self.bg_color)
        
        # External 5hr
        tk.Label(self.expanded_frame, text="外部模型 (5 小時用量)", bg=self.bg_color, fg="#AAAAAA", font=("Segoe UI", 8)).pack(anchor="w", pady=(5, 0))
        self.ext_lbl = tk.Label(self.expanded_frame, text="-- / -- (--%)", bg=self.bg_color, fg=self.fg_color, font=("Segoe UI", 9))
        self.ext_lbl.pack(anchor="w")
        
        # Gemini Weekly
        tk.Label(self.expanded_frame, text="Gemini (每週用量)", bg=self.bg_color, fg="#AAAAAA", font=("Segoe UI", 8)).pack(anchor="w", pady=(5, 0))
        self.gemini_weekly_lbl = tk.Label(self.expanded_frame, text="-- / -- (--%)", bg=self.bg_color, fg=self.fg_color, font=("Segoe UI", 9))
        self.gemini_weekly_lbl.pack(anchor="w")
        
        # Footer Frame
        self.footer = tk.Frame(self.main_frame, bg="#181818", height=30)
        self.footer.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.time_lbl = tk.Label(self.footer, text="上次更新: ---", bg="#181818", fg="#777777", font=("Segoe UI", 8))
        self.time_lbl.pack(side=tk.LEFT, padx=10, pady=5)
        
        refresh_lbl = tk.Label(self.footer, text="重新整理", bg="#181818", fg=self.accent_color, font=("Segoe UI", 8, "underline"), cursor="hand2")
        refresh_lbl.pack(side=tk.RIGHT, padx=10, pady=5)
        refresh_lbl.bind("<Button-1>", lambda e: self.trigger_refresh())

    # Window Dragging Logic
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def toggle_details(self):
        if self.show_details.get():
            self.show_details.set(False)
            self.cb_details.select()
            self.root.geometry(f"{self.width}x{self.expanded_height}")
            self.expanded_frame.pack(fill=tk.BOTH, expand=True, before=self.cb_details)
            self.cb_details.pack_forget()
            self.cb_details.pack(anchor="w", pady=(10, 0))
        else:
            self.show_details.set(True)
            self.cb_details.deselect()
            self.expanded_frame.pack_forget()
            self.root.geometry(f"{self.width}x{self.base_height}")

    def create_tray_icon(self):
        # Create a simple icon with a blue circle
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        dc.ellipse([8, 8, 56, 56], fill="#4FC3F7")
        dc.text((22, 22), "AGY", fill="black") # Requires a font to look good, but fine for basic
        return image

    def setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem('Show Widget', self.show_window, default=True),
            pystray.MenuItem('Refresh Now', self.trigger_refresh),
            pystray.MenuItem('Exit', self.exit_app)
        )
        self.icon = pystray.Icon("AGYMonitor", self.create_tray_icon(), "AGY Model Monitor", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        # Position at bottom right, slightly above taskbar
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - self.width - 20
        y = screen_height - (self.expanded_height if not self.show_details.get() else self.base_height) - 60
        self.root.geometry(f"+{x}+{y}")
        self.root.lift()

    def hide_window(self):
        self.root.withdraw()

    def exit_app(self, icon=None, item=None):
        self.icon.stop()
        self.root.quit()
        sys.exit(0)
        
    def trigger_refresh(self):
        if not self.is_fetching:
            self.time_lbl.config(text="更新中...")
            threading.Thread(target=self.fetch_and_update, daemon=True).start()
            
    def fetch_and_update(self):
        self.is_fetching = True
        try:
            data = data_fetcher.fetch_usage_data()
            self.root.after(0, self.update_ui_with_data, data)
        except Exception as e:
            self.root.after(0, lambda: self.time_lbl.config(text=f"錯誤: {str(e)[:15]}"))
        finally:
            self.is_fetching = False
            
    def update_ui_with_data(self, data):
        g = data.get("gemini", {})
        e = data.get("external", {})
        
        # Color based on remaining usage (Red if < 10%)
        g_color = self.warning_color if g.get("5hr_percent", 100) < 10 else self.accent_color
        
        self.gemini_pct_lbl.config(text=f"{g.get('5hr_percent', 0)}%", fg=g_color)
        self.gemini_text_lbl.config(text=f"重置時間: {g.get('reset_time_5h', '--')}")
        
        self.ext_lbl.config(text=f"剩餘: {e.get('5hr_percent', 0)}% (重置: {e.get('reset_time_5h', '--')})")
        self.gemini_weekly_lbl.config(text=f"剩餘: {g.get('weekly_percent', 0)}% (重置: {g.get('reset_time_weekly', '--')})")
        
        self.time_lbl.config(text=f"上次更新: {data.get('last_updated', '--')}")

    def auto_update_loop(self):
        while True:
            time.sleep(180) # 3 minutes
            self.trigger_refresh()

    def run(self):
        self.trigger_refresh()
        self.root.mainloop()

if __name__ == "__main__":
    app = UsageWidget()
    app.run()
