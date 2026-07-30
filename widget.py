import os
import sys
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
import pystray
from PIL import Image, ImageDraw
import data_fetcher
import history_logger

BG_COLOR = "#202124" # Dark theme background
ARC_BG = "#3C4043"
TEXT_FG = "#E8EAED"
TEXT_MUTED = "#9AA0A6"
COLOR_GEMINI = "#4FC3F7"
COLOR_GEMINI_WEEKLY = "#4FC3F7" # Same color family
COLOR_EXT = "#FFB74D"
COLOR_EXT_WEEKLY = "#FFB74D" # Same color family

class ArcGauge(tk.Canvas):
    def __init__(self, parent, size=140, title="Title", color="#4FC3F7", **kwargs):
        super().__init__(parent, width=size, height=size, bg=BG_COLOR, highlightthickness=0, **kwargs)
        self.size = size
        self.color = color
        self.arc_width = size * 0.12
        pad = self.arc_width + 5
        self.bbox = (pad, pad, size - pad, size - pad)
        
        # bg arc
        self.create_arc(*self.bbox, start=0, extent=180, style=tk.ARC, width=self.arc_width, outline=ARC_BG)
        # fg arc (dynamically updated)
        self.fg_arc = self.create_arc(*self.bbox, start=180, extent=0, style=tk.ARC, width=self.arc_width, outline=self.color)
        
        # Text elements
        self.pct_text = self.create_text(size/2, size/2 - 15, text="0%", fill=TEXT_FG, font=("Segoe UI", 18, "bold"))
        self.time_text = self.create_text(size/2, size/2 + 7, text="--h --m", fill=TEXT_MUTED, font=("Segoe UI", 9))
        self.title_text = self.create_text(size/2, size/2 + 32, text=title, fill=TEXT_FG, font=("Segoe UI", 9, "bold"), justify="center")

    def set_value(self, pct_remaining, reset_time):
        # pct_remaining is 0-100. We start at 180 (left) and sweep negative (clockwise)
        extent = -(180 * (pct_remaining / 100))
        self.itemconfig(self.fg_arc, extent=extent)
        self.itemconfig(self.pct_text, text=f"{int(pct_remaining)}%")
        
        # calculate remaining time text
        time_str = reset_time
        if reset_time and "Z" in reset_time:
            try:
                # e.g. '2026-07-30T08:38:06Z'
                dt = datetime.strptime(reset_time, "%Y-%m-%dT%H:%M:%SZ")
                now_utc = datetime.utcnow()
                if dt > now_utc:
                    delta = dt - now_utc
                    hours, remainder = divmod(delta.seconds, 3600)
                    minutes = remainder // 60
                    days = delta.days
                    if days > 0:
                        time_str = f"{days}d {hours}h"
                    else:
                        time_str = f"{hours}h {minutes}m"
                else:
                    time_str = "Resetting..."
            except:
                pass
        self.itemconfig(self.time_text, text=time_str)

class HistoryChart(tk.Canvas):
    def __init__(self, parent, width=300, height=80, **kwargs):
        super().__init__(parent, width=width, height=height, bg=BG_COLOR, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        
    def render(self, history):
        self.delete("all")
        if not history or len(history) < 2:
            self.create_text(self.width/2, self.height/2, text="等待數據收集中...", fill=TEXT_MUTED, font=("Segoe UI", 9))
            return
            
        # Draw dotted baseline
        y_base = self.height - 20
        self.create_line(10, y_base, self.width-10, y_base, fill=ARC_BG, dash=(2, 2))
        
        # Calculate deltas (burn rate per minute)
        deltas = []
        for i in range(1, len(history)):
            prev = history[i-1]
            curr = history[i]
            # usage = prev - curr (since it's remaining %)
            gem_burn = prev.get("gemini_5h", 100) - curr.get("gemini_5h", 100)
            ext_burn = prev.get("external_5h", 100) - curr.get("external_5h", 100)
            # prevent negative if resets
            gem_burn = max(0, gem_burn)
            ext_burn = max(0, ext_burn)
            deltas.append((gem_burn, ext_burn))
            
        if not deltas:
            return
            
        max_burn = max([g+e for g,e in deltas]) if deltas else 0
        if max_burn == 0:
            max_burn = 1 # avoid div by zero
            
        # Draw bars
        bar_w = 4
        spacing = 2
        total_bars = len(deltas)
        max_bars = int((self.width - 20) / (bar_w + spacing))
        
        display_deltas = deltas[-max_bars:]
        
        start_x = 10
        for g, e in display_deltas:
            h_g = (g / max_burn) * (self.height - 30)
            h_e = (e / max_burn) * (self.height - 30)
            
            # draw stacked bar (gemini on bottom, ext on top)
            if g > 0:
                self.create_rectangle(start_x, y_base - h_g, start_x + bar_w, y_base, fill=COLOR_GEMINI, outline="")
            if e > 0:
                self.create_rectangle(start_x, y_base - h_g - h_e, start_x + bar_w, y_base - h_g, fill=COLOR_EXT, outline="")
            
            # minimal dots for zero burn
            if g == 0 and e == 0:
                self.create_rectangle(start_x, y_base-2, start_x + bar_w, y_base, fill=ARC_BG, outline="")
                
            start_x += bar_w + spacing
            
        # Stats text
        avg_burn = sum([g+e for g,e in display_deltas]) / len(display_deltas)
        hourly_burn = avg_burn * 60 / 3 # assuming 3 min intervals
        
        # Usage history title
        self.create_text(10, 10, text="Usage History", fill=TEXT_MUTED, font=("Segoe UI", 9), anchor="w")
        self.create_text(self.width-10, 10, text=f"max: {round(max_burn, 1)}%", fill=TEXT_MUTED, font=("Segoe UI", 9), anchor="e")
        
        self.create_text(10, self.height-5, text=f"Last {len(display_deltas)*3} min", fill=TEXT_MUTED, font=("Segoe UI", 8), anchor="w")
        
        status_color = "#FF5252" if hourly_burn > 20 else ("#FFB74D" if hourly_burn > 10 else TEXT_MUTED)
        self.create_text(self.width-10, self.height-5, text=f"🔥 {round(hourly_burn, 1)}%/h", fill=status_color, font=("Segoe UI", 8), anchor="e")

class UsageWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AGY Fuel Gauge")
        self.root.geometry("340x280")
        self.root.configure(bg=BG_COLOR)
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.withdraw()
        
        self.width = 340
        self.base_height = 290
        
        # Variables for dragging
        self.x = 0
        self.y = 0
        
        self.build_ui()
        self.setup_tray()
        
        self.is_fetching = False
        self.update_thread = threading.Thread(target=self.auto_update_loop, daemon=True)
        self.update_thread.start()
        
    def build_ui(self):
        # Main container with border
        self.main_frame = tk.Frame(self.root, bg=BG_COLOR, highlightbackground="#3A3B3C", highlightthickness=1)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header (Drag handle)
        self.header = tk.Frame(self.main_frame, bg="#2D2D2D", height=24)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)
        self.header.bind("<ButtonPress-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)
        
        title = tk.Label(self.header, text="AGY Fuel Gauge", bg="#2D2D2D", fg=TEXT_FG, font=("Segoe UI", 9, "bold"))
        title.pack(side=tk.LEFT, padx=10, pady=5)
        title.bind("<ButtonPress-1>", self.start_move)
        title.bind("<B1-Motion>", self.do_move)
        
        # Refresh and close
        close_btn = tk.Label(self.header, text="X", bg="#2D2D2D", fg=TEXT_MUTED, font=("Segoe UI", 9, "bold"), cursor="hand2")
        close_btn.pack(side=tk.RIGHT, padx=10)
        close_btn.bind("<Button-1>", lambda e: self.hide_window())
        
        refresh_btn = tk.Label(self.header, text="↻", bg="#2D2D2D", fg=TEXT_MUTED, font=("Segoe UI", 12), cursor="hand2")
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        refresh_btn.bind("<Button-1>", lambda e: self.trigger_refresh())
        
        self.content = tk.Frame(self.main_frame, bg=BG_COLOR, padx=10, pady=5)
        self.content.pack(fill=tk.BOTH, expand=True)
        
        # Container for Arcs to keep height constant
        self.arcs_container = tk.Frame(self.content, bg=BG_COLOR)
        self.arcs_container.pack(fill=tk.X)
        
        # Top Arcs (5hr limits)
        self.top_arcs_frame = tk.Frame(self.arcs_container, bg=BG_COLOR)
        self.top_arcs_frame.pack(fill=tk.X)
        
        self.gemini_5h_gauge = ArcGauge(self.top_arcs_frame, size=150, title="Gemini\n(5h)", color=COLOR_GEMINI)
        self.gemini_5h_gauge.pack(side=tk.LEFT, padx=5)
        
        self.ext_5h_gauge = ArcGauge(self.top_arcs_frame, size=150, title="External\n(5h)", color=COLOR_EXT)
        self.ext_5h_gauge.pack(side=tk.RIGHT, padx=5)
        
        # Bottom Arcs (Weekly limits) - Hidden by default
        self.weekly_arcs_frame = tk.Frame(self.arcs_container, bg=BG_COLOR)
        
        self.gemini_w_gauge = ArcGauge(self.weekly_arcs_frame, size=150, title="Gemini\n(Weekly)", color=COLOR_GEMINI_WEEKLY)
        self.gemini_w_gauge.pack(side=tk.LEFT, padx=5)
        
        self.ext_w_gauge = ArcGauge(self.weekly_arcs_frame, size=150, title="External\n(Weekly)", color=COLOR_EXT_WEEKLY)
        self.ext_w_gauge.pack(side=tk.RIGHT, padx=5)
        
        # Collapsible Toggle
        self.toggle_btn = tk.Label(self.content, text="▶ Weekly", bg=BG_COLOR, fg=TEXT_MUTED, font=("Segoe UI", 9), cursor="hand2")
        self.toggle_btn.pack(pady=2)
        self.toggle_btn.bind("<Button-1>", self.toggle_weekly)
        self.show_weekly = False
        
        # History Chart
        self.chart_frame = tk.Frame(self.content, bg="#2A2B2E", bd=1, relief="solid")
        self.chart_frame.pack(fill=tk.X, pady=(5, 0), padx=5)
        
        self.chart = HistoryChart(self.chart_frame, width=310, height=85)
        self.chart.pack(padx=5, pady=5)
        
        # Fixed height
        self.root.geometry(f"{self.width}x{self.base_height}")

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def toggle_weekly(self, event=None):
        self.show_weekly = not self.show_weekly
        if self.show_weekly:
            self.toggle_btn.config(text="◀ 5h")
            self.top_arcs_frame.pack_forget()
            self.weekly_arcs_frame.pack(fill=tk.X)
        else:
            self.toggle_btn.config(text="▶ Weekly")
            self.weekly_arcs_frame.pack_forget()
            self.top_arcs_frame.pack(fill=tk.X)

    def create_tray_icon(self):
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        dc.ellipse([8, 8, 56, 56], fill=COLOR_GEMINI)
        dc.text((22, 22), "AGY", fill="black")
        return image

    def setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem('Show Widget', self.show_window, default=True),
            pystray.MenuItem('Refresh Now', self.trigger_refresh),
            pystray.MenuItem('Exit', self.exit_app)
        )
        self.icon = pystray.Icon("AGYMonitor", self.create_tray_icon(), "AGY Toolkit", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        current_h = self.base_height
        x = screen_width - self.width - 20
        y = screen_height - current_h - 60
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
            threading.Thread(target=self.fetch_and_update, daemon=True).start()
            
    def fetch_and_update(self):
        self.is_fetching = True
        try:
            data = data_fetcher.fetch_usage_data()
            self.root.after(0, self.update_ui_with_data, data)
        except Exception as e:
            pass # Silently fail and wait for next tick
        finally:
            self.is_fetching = False
            
    def update_ui_with_data(self, data):
        g = data.get("gemini", {})
        e = data.get("external", {})
        
        self.gemini_5h_gauge.set_value(g.get("5hr_percent", 0), g.get("reset_time_5h", "--"))
        self.ext_5h_gauge.set_value(e.get("5hr_percent", 0), e.get("reset_time_5h", "--"))
        
        self.gemini_w_gauge.set_value(g.get("weekly_percent", 0), g.get("reset_time_weekly", "--"))
        self.ext_w_gauge.set_value(e.get("weekly_percent", 0), e.get("reset_time_weekly", "--"))
        
        # Render history
        history = history_logger.get_history(minutes=180) # Last 3 hours
        self.chart.render(history)

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
