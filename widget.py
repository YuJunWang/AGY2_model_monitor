import os
import sys
import threading
import time
import tkinter as tk
import ctypes
from datetime import datetime, timedelta
import pystray
from PIL import Image, ImageDraw
import math

# ── Single Instance Lock ───────────────────────────────────────────────────
mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\AGY_Fuel_Gauge_Mutex")
if ctypes.windll.kernel32.GetLastError() == 183: # ERROR_ALREADY_EXISTS
    sys.exit(0)

import data_fetcher
import history_logger

TRANSPARENT_COLOR = "#000001"
BG_COLOR       = "#12141A"
HEADER_COLOR   = "#1A1D24"
SURFACE_COLOR  = "#171A21"
TRACK_BG       = "#262B33"
TEXT_FG        = "#F0F2F4"
TEXT_MUTED     = "#7A8086"
COLOR_GEMINI        = "#29B6F6"
COLOR_GEMINI_GLOW   = "#E1F5FE"
COLOR_GEMINI_MID    = "#0277BD"
COLOR_EXT           = "#FFA726"
COLOR_EXT_GLOW      = "#FFF8E1"
COLOR_EXT_MID       = "#E65100"
DIGITAL_FONT        = "Consolas" # Monospace dashboard font

class VerticalFuelGauge(tk.Canvas):
    def __init__(self, parent, width=40, height=200, title="Title", base_color=COLOR_GEMINI_MID, core_color=COLOR_GEMINI, tip_color=COLOR_GEMINI_GLOW, **kwargs):
        super().__init__(parent, width=width, height=height, bg=BG_COLOR, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.base_color = base_color
        self.core_color = core_color
        self.tip_color = tip_color
        
        # Dimensions for the vertical bar
        self.bar_width = 12
        self.padding_top = 35
        self.padding_bottom = 40
        
        self.cx = self.width / 2
        self.y_bottom = self.height - self.padding_bottom
        self.y_top = self.padding_top
        self.track_height = self.y_bottom - self.y_top
        
        # Track
        self.create_line(self.cx, self.y_bottom, self.cx, self.y_top, fill=TRACK_BG, width=self.bar_width, capstyle=tk.ROUND)
        
        # Reverted Glow (Base + Core)
        self.line_base = self.create_line(self.cx, self.y_bottom, self.cx, self.y_bottom, fill=self.base_color, width=self.bar_width, capstyle=tk.ROUND)
        self.line_core = self.create_line(self.cx, self.y_bottom, self.cx, self.y_bottom, fill=self.core_color, width=self.bar_width - 4, capstyle=tk.ROUND)
        self.tip_dot = self.create_oval(0, 0, 0, 0, fill=self.tip_color, outline="", state="hidden")
        
        # Percentage (Consolas/Digital style)
        self.pct_text = self.create_text(self.cx, self.y_bottom + 18, text="--%", fill=self.core_color, font=(DIGITAL_FONT, 10, "bold"), justify="center")
        self.title_text = self.create_text(self.cx, self.y_top - 16, text=title, fill=TEXT_MUTED, font=("Segoe UI", 8, "bold"), justify="center")
        
        # Rotated time text placed right next to the bar
        # Changed to Segoe UI 9 for better legibility (not bold to avoid smudging)
        self.time_text = self.create_text(self.cx + 15, self.height / 2, text="--h", fill=TEXT_MUTED, font=("Segoe UI", 9), justify="center", angle=270)

    def set_value(self, pct_remaining, reset_time):
        val = max(0.0, min(100.0, pct_remaining))
        fill_height = self.track_height * (val / 100.0)
        curr_y = self.y_bottom - fill_height
        
        self.coords(self.line_base, self.cx, self.y_bottom, self.cx, curr_y)
        self.coords(self.line_core, self.cx, self.y_bottom, self.cx, curr_y)
        
        if val > 0:
            r = (self.bar_width - 4) / 2
            self.coords(self.tip_dot, self.cx - r, curr_y - r, self.cx + r, curr_y + r)
            self.itemconfig(self.tip_dot, state="normal")
        else:
            self.itemconfig(self.tip_dot, state="hidden")
            
        self.itemconfig(self.pct_text, text=f"{int(val)}%")
        if val <= 20:
            self.itemconfig(self.pct_text, fill="#FF5252")
        elif val <= 50:
            self.itemconfig(self.pct_text, fill="#FDD835")
        else:
            self.itemconfig(self.pct_text, fill=self.core_color)
            
        time_str = reset_time
        if reset_time and "Z" in reset_time:
            try:
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
                    time_str = "Reset..."
            except Exception:
                pass
        self.itemconfig(self.time_text, text=time_str)

class VerticalHistoryChart(tk.Canvas):
    def __init__(self, parent, width=100, height=140, **kwargs):
        super().__init__(parent, width=width, height=height, bg=SURFACE_COLOR, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        
    def render(self, history):
        self.delete("all")
        if not history or len(history) < 2:
            self.create_text(self.width/2, self.height/2, text="Waiting...", fill=TEXT_MUTED, font=("Segoe UI", 7))
            return
            
        mid_x = self.width / 2
        y_top = 10
        y_bottom = self.height - 15  # leave room for -6H label at the bottom
        
        # Center axis line
        self.create_line(mid_x, y_top, mid_x, y_bottom, fill="#3A3D42", dash=(2, 2))
        
        # Time Ticks (Every 1h small, every 2h big)
        y_range = y_bottom - y_top
        for h in range(1, 6):
            tick_y = y_top + (h / 6.0) * y_range
            if h % 2 == 0:
                # 2H, 4H (Big tick)
                self.create_line(mid_x - 3, tick_y, mid_x + 3, tick_y, fill=TEXT_FG, width=1.5)
            else:
                # 1H, 3H, 5H (Small tick)
                self.create_line(mid_x - 1.5, tick_y, mid_x + 1.5, tick_y, fill=TEXT_MUTED, width=1.0)
        
        parsed = []
        for r in history:
            try:
                ts = datetime.fromisoformat(r["timestamp"])
                parsed.append((ts, r.get("gemini_5h", 100), r.get("external_5h", 100)))
            except Exception:
                continue
        parsed.sort(key=lambda x: x[0])
        if len(parsed) < 2:
            return
            
        now = datetime.now()
        BUCKET_MIN = 3
        NUM_BUCKETS = 120
        
        buckets = [] 
        for i in range(0, NUM_BUCKETS):
            b_end = now - timedelta(minutes=i * BUCKET_MIN)
            b_start = now - timedelta(minutes=(i + 1) * BUCKET_MIN)
            
            before = [(ts, g, e) for ts, g, e in parsed if ts <= b_start]
            in_win = [(ts, g, e) for ts, g, e in parsed if b_start < ts <= b_end]
            
            if in_win:
                ref_g, ref_e = (before[-1][1], before[-1][2]) if before else (in_win[0][1], in_win[0][2])
                end_g, end_e = in_win[-1][1], in_win[-1][2]
                gem_drop = max(0, ref_g - end_g)
                ext_drop = max(0, ref_e - end_e)
            else:
                gem_drop = 0
                ext_drop = 0
            buckets.append((gem_drop, ext_drop))
            
        gem_vals = [g for g, e in buckets]
        ext_vals = [e for g, e in buckets]
        gem_max = max(gem_vals) if any(v > 0 for v in gem_vals) else 1
        ext_max = max(ext_vals) if any(v > 0 for v in ext_vals) else 1
        
        zone_w = (mid_x - 5)
        step_y = y_range / NUM_BUCKETS
        
        gem_pts = []
        ext_pts = []
        
        for idx, (g, e) in enumerate(buckets):
            cy = y_top + (idx + 0.5) * step_y
            w_g = (g / gem_max) * zone_w
            w_e = (e / ext_max) * zone_w
            gem_pts.append((mid_x - w_g, cy))
            ext_pts.append((mid_x + w_e, cy))
            
        # Draw Gemini Fill (Slightly brighter so it's clearly filled to center)
        poly_gem = [(mid_x, y_top)] + gem_pts + [(mid_x, y_bottom), (mid_x, y_top)]
        self.create_polygon(poly_gem, fill="#0F3352", outline="")
        if len(gem_pts) > 1:
            self.create_line(gem_pts, fill=COLOR_GEMINI_MID, width=1.5, smooth=True)
            
        # Draw External Fill (Slightly brighter)
        poly_ext = [(mid_x, y_top)] + ext_pts + [(mid_x, y_bottom), (mid_x, y_top)]
        self.create_polygon(poly_ext, fill="#4A2A0A", outline="")
        if len(ext_pts) > 1:
            self.create_line(ext_pts, fill=COLOR_EXT_MID, width=1.5, smooth=True)
            
        gem_total = sum(g for g, e in buckets)
        ext_total = sum(e for g, e in buckets)
        gem_hourly = gem_total / 6.0
        ext_hourly = ext_total / 6.0

        gem_color = "#FF5252" if gem_hourly > 20 else COLOR_GEMINI
        ext_color = "#FF5252" if ext_hourly > 20 else COLOR_EXT
        
        # Floating Burn Rates (Reading top-to-bottom)
        self.create_text(8, self.height / 2, text=f"{round(gem_hourly, 1)}%/h", fill=gem_color, font=(DIGITAL_FONT, 8, "bold"), angle=270, anchor="center")
        self.create_text(self.width-8, self.height / 2, text=f"{round(ext_hourly, 1)}%/h", fill=ext_color, font=(DIGITAL_FONT, 8, "bold"), angle=270, anchor="center")
        
        # -6H label pushed all the way to the bottom edge
        self.create_text(mid_x, self.height - 2, text="-6H", fill=TEXT_MUTED, font=("Segoe UI", 6), anchor="s")

class UsageWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AGY Fuel Gauge")
        
        # Total width 134 (24 tab + 110 main)
        self.width = 134
        self.base_height = 500
        self.root.geometry(f"{self.width}x{self.base_height}")
        
        # We use SetWindowRgn for the precise shape, so no transparent color is needed
        self.root.configure(bg=BG_COLOR)
        
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.82)
        
        # Create true L-shaped rounded window region using Windows API
        self.root.update_idletasks()
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            # Main body: x=24 to 134, y=0 to 500, with 12px rounding (6px radius)
            rgn_main = ctypes.windll.gdi32.CreateRoundRectRgn(24, 0, 134, 500, 12, 12)
            # Tab: x=0 to 30, y=0 to 140
            rgn_tab = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, 30, 140, 12, 12)
            
            # Patch regions to fix the notches created by overlapping rounded corners
            rgn_top_patch = ctypes.windll.gdi32.CreateRectRgn(10, 0, 40, 12)      # Straight top edge
            rgn_inner_patch = ctypes.windll.gdi32.CreateRectRgn(24, 120, 30, 150) # Sharp inner corner
            
            # Combine them all
            rgn_combined = ctypes.windll.gdi32.CreateRectRgn(0, 0, 0, 0)
            ctypes.windll.gdi32.CombineRgn(rgn_combined, rgn_main, rgn_tab, 2) # RGN_OR
            ctypes.windll.gdi32.CombineRgn(rgn_combined, rgn_combined, rgn_top_patch, 2)
            ctypes.windll.gdi32.CombineRgn(rgn_combined, rgn_combined, rgn_inner_patch, 2)
            
            ctypes.windll.user32.SetWindowRgn(hwnd, rgn_combined, True)
        except Exception as e:
            pass
            
        self.root.withdraw()
        
        self.x = 0
        self.y = 0
        
        self.build_ui()
        self.setup_tray()
        
        self.is_fetching = False
        self.update_thread = threading.Thread(target=self.auto_update_loop, daemon=True)
        self.update_thread.start()
        
    def build_ui(self):
        # ── Protruding Tab (Top Left) ────────
        self.tab_canvas = tk.Canvas(self.root, width=24, height=140, bg=BG_COLOR, highlightthickness=0)
        self.tab_canvas.place(x=0, y=0)
        self.tab_canvas.bind("<ButtonPress-1>", self.start_move)
        self.tab_canvas.bind("<B1-Motion>", self.do_move)
        
        # Vertical Text reading top-to-bottom
        self.tab_canvas.create_text(12, 70, text="AGY FUEL GAUGE", fill=TEXT_MUTED, font=("Segoe UI", 8, "bold"), angle=270)
        
        # ── Main Content Body ──────────────────────────
        self.main_frame = tk.Frame(self.root, bg=BG_COLOR, highlightthickness=0)
        self.main_frame.place(x=24, y=0, width=110, height=self.base_height)

        # Header
        self.header = tk.Frame(self.main_frame, bg=HEADER_COLOR, height=24)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)
        self.header.bind("<ButtonPress-1>", self.start_move)
        self.header.bind("<B1-Motion>", self.do_move)
        
        close_btn = tk.Label(self.header, text="✕", bg=HEADER_COLOR, fg=TEXT_MUTED, font=("Segoe UI", 8), cursor="hand2")
        close_btn.pack(side=tk.RIGHT, padx=6)
        close_btn.bind("<Button-1>", lambda e: self.hide_window())
        
        self.refresh_btn = tk.Label(self.header, text="↻", bg=HEADER_COLOR, fg=TEXT_MUTED, font=("Segoe UI", 9), cursor="hand2")
        self.refresh_btn.pack(side=tk.RIGHT, padx=2)
        self.refresh_btn.bind("<Button-1>", lambda e: self.trigger_refresh())
        
        self.last_update_lbl = tk.Label(self.header, text="--:--", bg=HEADER_COLOR, fg=TEXT_MUTED, font=(DIGITAL_FONT, 7))
        self.last_update_lbl.pack(side=tk.LEFT, padx=6)

        # Toggle
        self.toggle_container = tk.Frame(self.main_frame, bg="#1E2129", padx=2, pady=2, bd=0)
        self.toggle_container.pack(pady=8)
        seg_font = ("Segoe UI", 7, "bold")
        self.btn_5h = tk.Label(self.toggle_container, text=" 5H ", font=seg_font, bg="#333842", fg=TEXT_FG, cursor="hand2", padx=6, pady=2)
        self.btn_5h.pack(side=tk.LEFT)
        self.btn_5h.bind("<Button-1>", lambda e: self.set_view(False))
        self.btn_weekly = tk.Label(self.toggle_container, text=" WK ", font=seg_font, bg="#1E2129", fg=TEXT_MUTED, cursor="hand2", padx=6, pady=2)
        self.btn_weekly.pack(side=tk.LEFT)
        self.btn_weekly.bind("<Button-1>", lambda e: self.set_view(True))
        
        self.show_weekly = False
        
        # Vertical Fuel Bars
        self.bars_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.bars_frame.pack(fill=tk.X, pady=4)
        
        self.view_5h_frame = tk.Frame(self.bars_frame, bg=BG_COLOR)
        self.view_5h_frame.pack(fill=tk.X)
        self.gemini_5h_gauge = VerticalFuelGauge(self.view_5h_frame, width=50, height=210, title="GEM", base_color=COLOR_GEMINI_MID, core_color=COLOR_GEMINI, tip_color=COLOR_GEMINI_GLOW)
        self.gemini_5h_gauge.pack(side=tk.LEFT)
        self.ext_5h_gauge = VerticalFuelGauge(self.view_5h_frame, width=50, height=210, title="EXT", base_color=COLOR_EXT_MID, core_color=COLOR_EXT, tip_color=COLOR_EXT_GLOW)
        self.ext_5h_gauge.pack(side=tk.RIGHT)
        
        self.view_wk_frame = tk.Frame(self.bars_frame, bg=BG_COLOR)
        self.gemini_wk_gauge = VerticalFuelGauge(self.view_wk_frame, width=50, height=210, title="GEM", base_color="#0277BD", core_color="#29B6F6", tip_color="#81D4FA")
        self.gemini_wk_gauge.pack(side=tk.LEFT)
        self.ext_wk_gauge = VerticalFuelGauge(self.view_wk_frame, width=50, height=210, title="EXT", base_color="#D84315", core_color="#FF7043", tip_color="#FFAB91")
        self.ext_wk_gauge.pack(side=tk.RIGHT)

        # Vertical History Chart
        self.chart_frame = tk.Frame(self.main_frame, bg=SURFACE_COLOR, bd=0, highlightthickness=0)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 8), padx=6)
        
        self.chart = VerticalHistoryChart(self.chart_frame, width=96, height=190)
        self.chart.pack(fill=tk.BOTH, expand=True)
        
        history = history_logger.get_history(minutes=360)
        self.chart.render(history)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def set_view(self, show_weekly):
        if self.show_weekly == show_weekly: return
        self.show_weekly = show_weekly
        if self.show_weekly:
            self.btn_5h.config(bg="#1E2129", fg=TEXT_MUTED)
            self.btn_weekly.config(bg="#333842", fg=TEXT_FG)
            self.view_5h_frame.pack_forget()
            self.view_wk_frame.pack(fill=tk.X)
        else:
            self.btn_weekly.config(bg="#1E2129", fg=TEXT_MUTED)
            self.btn_5h.config(bg="#333842", fg=TEXT_FG)
            self.view_wk_frame.pack_forget()
            self.view_5h_frame.pack(fill=tk.X)

    def create_tray_icon(self):
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
            return Image.open(icon_path)
        except Exception:
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            dc = ImageDraw.Draw(img)
            dc.ellipse([8, 8, 56, 56], fill=COLOR_GEMINI)
            return img

    def setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem('Show Widget', self.show_window, default=True),
            pystray.MenuItem('Refresh Now', self.trigger_refresh),
            pystray.MenuItem('Exit', self.exit_app)
        )
        self.icon = pystray.Icon("AGYMonitor", self.create_tray_icon(), "AGY Fuel Gauge", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - self.width - 20
        y = screen_height - self.base_height - 60
        self.root.geometry(f"+{x}+{y}")
        self.root.lift()
        self.trigger_refresh()

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
        self.root.after(0, lambda: self.refresh_btn.config(fg=COLOR_GEMINI_GLOW))
        try:
            data = data_fetcher.fetch_usage_data()
            self.root.after(0, self.update_ui_with_data, data)
        except Exception as e:
            print(f"[AGY Fuel Gauge] Fetch failed: {e}")
        finally:
            self.is_fetching = False
            self.root.after(0, lambda: self.refresh_btn.config(fg=TEXT_MUTED))
            
    def update_ui_with_data(self, data):
        now_str = datetime.now().strftime("%H:%M")
        self.last_update_lbl.config(text=f"{now_str}")
        
        g = data.get("gemini", {})
        e = data.get("external", {})
        
        self.gemini_5h_gauge.set_value(g.get("5hr_percent", 0), g.get("reset_time_5h", "--"))
        self.ext_5h_gauge.set_value(e.get("5hr_percent", 0), e.get("reset_time_5h", "--"))
        
        self.gemini_wk_gauge.set_value(g.get("weekly_percent", 0), g.get("reset_time_weekly", "--"))
        self.ext_wk_gauge.set_value(e.get("weekly_percent", 0), e.get("reset_time_weekly", "--"))
        
        history = history_logger.get_history(minutes=360)
        self.chart.render(history)

    def auto_update_loop(self):
        while True:
            time.sleep(180)
            self.trigger_refresh()

    def run(self):
        self.show_window()
        self.root.mainloop()

if __name__ == "__main__":
    app = UsageWidget()
    app.run()
