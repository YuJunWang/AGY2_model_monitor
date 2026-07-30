import os
import sys
import threading
import time
import tkinter as tk
import ctypes
import sys
from datetime import datetime, timedelta
import pystray
from PIL import Image, ImageDraw

# ── Single Instance Lock ───────────────────────────────────────────────────
mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\AGY_Fuel_Gauge_Mutex")
if ctypes.windll.kernel32.GetLastError() == 183: # ERROR_ALREADY_EXISTS
    sys.exit(0)

import data_fetcher
import history_logger

BG_COLOR       = "#121212"  # OLED Deep Dark
HEADER_COLOR   = "#1E1E1E"  # Slightly lighter header
SURFACE_COLOR  = "#1A1A1A"  # Card/chart surface
ARC_BG         = "#2E3033"  # Dimmed arc track
TEXT_FG        = "#F0F2F4"  # Near-white primary text
TEXT_MUTED     = "#7A8086"  # Muted secondary text
COLOR_GEMINI        = "#29B6F6"  # Bright sky blue
COLOR_GEMINI_GLOW   = "#81D4FA"  # Lighter blue for glow tip
COLOR_GEMINI_WEEKLY = "#0288D1"
COLOR_EXT           = "#FFA726"  # Warm amber
COLOR_EXT_GLOW      = "#FFE082"  # Light amber for glow tip
COLOR_EXT_WEEKLY    = "#E65100"

class ArcGauge(tk.Canvas):
    def __init__(self, parent, size=140, title="Title", color="#29B6F6", glow_color="#81D4FA", **kwargs):
        super().__init__(parent, width=size, height=size, bg=BG_COLOR, highlightthickness=0, **kwargs)
        self.size = size
        self.color = color
        self.glow_color = glow_color
        self.arc_width = size * 0.12
        pad = self.arc_width + 5
        self.bbox = (pad, pad, size - pad, size - pad)
        self._pct = 0  # Track current percentage for glow dot calc
        
        # 270° arc: gap opens at the bottom (225° → clockwise → 315°)
        # bg arc track: start=225°, sweep -270° clockwise to 315°
        self.create_arc(*self.bbox, start=225, extent=-270, style=tk.ARC, width=self.arc_width, outline=ARC_BG)
        # fg arc: starts at 225°, extent grows clockwise (negative)
        self.fg_arc = self.create_arc(*self.bbox, start=225, extent=0, style=tk.ARC, width=self.arc_width, outline=self.color)
        # Glow dot at arc tip (drawn after arc so it's on top)
        self.glow_outer = self.create_oval(0, 0, 0, 0, fill=self.glow_color, outline="", state="hidden")
        self.glow_inner = self.create_oval(0, 0, 0, 0, fill="#FFFFFF",       outline="", state="hidden")
        
        # Text elements — vertically centered in the enclosed area
        self.pct_text  = self.create_text(size/2, size/2 - 8,  text="--%",    fill=TEXT_FG,    font=("Segoe UI", 20, "bold"))
        self.time_text = self.create_text(size/2, size/2 + 14,  text="--h --m", fill=TEXT_MUTED, font=("Segoe UI", 8))
        self.title_text= self.create_text(size/2, size/2 + 38,  text=title,    fill=TEXT_MUTED, font=("Segoe UI", 9, "bold"), justify="center")

    def set_value(self, pct_remaining, reset_time):
        import math
        self._pct = pct_remaining
        # Arc: starts at 225° (lower-left), sweeps -270° clockwise at 100%
        extent = -(270 * (pct_remaining / 100))
        self.itemconfig(self.fg_arc, extent=extent)
        
        # ── Glow dot at the tip of the arc ────────────────────────────────
        cx = (self.bbox[0] + self.bbox[2]) / 2
        cy = (self.bbox[1] + self.bbox[3]) / 2
        rx = (self.bbox[2] - self.bbox[0]) / 2
        ry = (self.bbox[3] - self.bbox[1]) / 2
        # Tip angle = start (225°) + extent (clockwise = negative)
        angle_deg = 225 + extent  # Tkinter angle: CCW from 3-o'clock
        angle_rad = math.radians(angle_deg)
        tip_x = cx + rx * math.cos(angle_rad)
        tip_y = cy - ry * math.sin(angle_rad)
        r_outer = self.arc_width * 0.55
        r_inner = self.arc_width * 0.22
        if pct_remaining > 1:
            self.coords(self.glow_outer, tip_x - r_outer, tip_y - r_outer, tip_x + r_outer, tip_y + r_outer)
            self.coords(self.glow_inner, tip_x - r_inner, tip_y - r_inner, tip_x + r_inner, tip_y + r_inner)
            self.itemconfig(self.glow_outer, state="normal")
            self.itemconfig(self.glow_inner, state="normal")
        else:
            self.itemconfig(self.glow_outer, state="hidden")
            self.itemconfig(self.glow_inner, state="hidden")
        
        # ── Percentage text with glow color ───────────────────────────────
        self.itemconfig(self.pct_text, text=f"{int(pct_remaining)}%")
        if pct_remaining <= 20:
            pct_color = "#FF5252"   # red — critical
        elif pct_remaining <= 50:
            pct_color = "#FDD835"   # yellow — warning
        else:
            pct_color = self.glow_color  # Use the arc's glow color (blue/amber)
        self.itemconfig(self.pct_text, fill=pct_color)
        
        # ── Reset time text ────────────────────────────────────────────────
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
                    time_str = "Resetting..."
            except Exception:
                pass
        self.itemconfig(self.time_text, text=time_str)

class HistoryChart(tk.Canvas):
    def __init__(self, parent, width=300, height=90, **kwargs):
        super().__init__(parent, width=width, height=height, bg=SURFACE_COLOR, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        
    def render(self, history):
        self.delete("all")
        if not history or len(history) < 2:
            self.create_text(self.width/2, self.height/2, text="Waiting for data...", fill=TEXT_MUTED, font=("Segoe UI", 9))
            return
        
        y_base = self.height - 22
        # Subtle horizontal grid line at base
        self.create_line(10, y_base, self.width-10, y_base, fill="#2A2B2E", dash=(3, 4))
        
        # Parse and sort all history entries by timestamp
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
        
        # ── Fixed 3-min bucket rendering ──────────────────────────────────────────
        # Regardless of how many refreshes happened, each bucket represents exactly
        # one 3-minute window. Manual refreshes cannot pollute the chart.
        now = datetime.now()
        BUCKET_MIN = 3
        NUM_BUCKETS = 120  # 6 hours
        
        buckets = []  # index 0 = oldest (6h ago), index -1 = newest
        for i in range(NUM_BUCKETS, 0, -1):
            b_start = now - timedelta(minutes=i * BUCKET_MIN)
            b_end   = now - timedelta(minutes=(i - 1) * BUCKET_MIN)
            
            # Reference: last reading at or before bucket start
            before  = [(ts, g, e) for ts, g, e in parsed if ts <= b_start]
            in_win  = [(ts, g, e) for ts, g, e in parsed if b_start < ts <= b_end]
            
            if in_win:
                ref_g, ref_e = (before[-1][1], before[-1][2]) if before else (in_win[0][1], in_win[0][2])
                end_g, end_e = in_win[-1][1], in_win[-1][2]
                gem_drop = max(0, ref_g - end_g)
                ext_drop = max(0, ref_e - end_e)
            else:
                gem_drop = 0
                ext_drop = 0
            
            buckets.append((gem_drop, ext_drop))
        
        max_val = max((g + e for g, e in buckets), default=1)
        if max_val == 0:
            max_val = 1
        
        # ── Mirrored Area Chart (Self-Normalized Waveform) ────────────────────────
        # Gemini grows UP from the middle (top half)
        # External grows DOWN from the middle (bottom half)
        # Both scale to their own local maximums, so they never crush each other.
        step_x = (self.width - 20) / NUM_BUCKETS
        
        # Define strict vertical boundaries to prevent overflow
        y_top    = 18          # top boundary (below labels)
        y_bottom = y_base - 2  # bottom boundary (above time axis)
        mid_y    = (y_top + y_bottom) // 2
        zone_h   = (mid_y - y_top) - 2   # max height per half, with 2px safety margin

        gem_vals = [g for g, e in buckets]
        ext_vals = [e for g, e in buckets]
        gem_max = max(gem_vals) if any(v > 0 for v in gem_vals) else 1
        ext_max = max(ext_vals) if any(v > 0 for v in ext_vals) else 1

        gem_pts = []
        ext_pts = []

        for idx, (g, e) in enumerate(buckets):
            cx = 10 + (idx + 0.5) * step_x
            h_g = (g / gem_max) * zone_h
            h_e = (e / ext_max) * zone_h
            gem_pts.append((cx, mid_y - h_g))   # Gemini grows UP from center
            ext_pts.append((cx, mid_y + h_e))   # External grows DOWN from center

        # Draw Gemini area (Top half, growing UP) — cool blue fill
        poly_gem = [(10, mid_y)] + gem_pts + [(self.width - 10, mid_y)]
        self.create_polygon(poly_gem, fill="#0A1F30", outline="")  # dark blue fill
        if len(gem_pts) > 1:
            self.create_line(gem_pts, fill=COLOR_GEMINI_GLOW, width=1.5, smooth=True)

        # Draw External area (Bottom half, growing DOWN) — warm amber fill
        poly_ext = [(10, mid_y)] + ext_pts + [(self.width - 10, mid_y)]
        self.create_polygon(poly_ext, fill="#3D2A0A", outline="")  # dark amber fill
        if len(ext_pts) > 1:
            self.create_line(ext_pts, fill=COLOR_EXT_GLOW, width=1.5, smooth=True)

        # Mirror axis
        self.create_line(10, mid_y, self.width - 10, mid_y, fill="#333639", dash=(3, 3))



        # ── Labels ────────────────────────────────────────────────────────────────
        self.create_text(10, 10, text="Usage History", fill=TEXT_MUTED, font=("Segoe UI", 8, "bold"), anchor="w")
        
        # Calculate separate burn rates
        gem_total = sum(g for g, e in buckets)
        ext_total = sum(e for g, e in buckets)
        gem_hourly = gem_total / 6.0
        ext_hourly = ext_total / 6.0

        # External Burn Rate
        ext_color = "#FF5252" if ext_hourly > 20 else COLOR_EXT
        ext_str = f"Ext: {round(ext_hourly, 1)}%/h"
        ext_id = self.create_text(self.width - 16, 10, text=ext_str, fill=ext_color, font=("Segoe UI", 8, "bold"), anchor="e")
        
        # Gemini Burn Rate
        bbox = self.bbox(ext_id)
        ext_w = bbox[2] - bbox[0] if bbox else 50
        
        gem_color = "#FF5252" if gem_hourly > 20 else COLOR_GEMINI
        gem_str = f"Gem: {round(gem_hourly, 1)}%/h"
        self.create_text(self.width - 16 - ext_w - 12, 10, text=gem_str, fill=gem_color, font=("Segoe UI", 8, "bold"), anchor="e")
        
        # Time axis: -6h (left), tick marks at -4h & -2h, now (right)
        self.create_text(12, self.height - 5, text="-6h", fill=TEXT_MUTED, font=("Segoe UI", 7), anchor="w")
        self.create_text(self.width - 16, self.height - 5, text="now", fill=TEXT_MUTED, font=("Segoe UI", 7), anchor="e")
        for bucket_idx, label in [(40, "-4h"), (80, "-2h")]:
            mark_x = 10 + (bucket_idx + 0.5) * step_x
            self.create_line(mark_x, y_base - 4, mark_x, y_base, fill=ARC_BG)
            self.create_text(mark_x, self.height - 5, text=label, fill=TEXT_MUTED, font=("Segoe UI", 7), anchor="center")
        
        return  # end of render


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
        self.main_frame = tk.Frame(self.root, bg=BG_COLOR, highlightbackground="#333333", highlightthickness=1)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title bar (draggable)
        self.header = tk.Frame(self.main_frame, bg=HEADER_COLOR, height=30)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)
        
        title = tk.Label(self.header, text="AGY Fuel Gauge", bg=HEADER_COLOR, fg=TEXT_FG, font=("Segoe UI", 10, "bold"))
        title.pack(side=tk.LEFT, padx=10, pady=5)
        title.bind("<ButtonPress-1>", self.start_move)
        title.bind("<B1-Motion>", self.do_move)
        
        # Refresh and close buttons
        close_btn = tk.Label(self.header, text="✕", bg=HEADER_COLOR, fg=TEXT_MUTED, font=("Segoe UI", 10), cursor="hand2")
        close_btn.pack(side=tk.RIGHT, padx=10)
        close_btn.bind("<Button-1>", lambda e: self.hide_window())
        self._bind_hover(close_btn, TEXT_MUTED, "#FF5252")  # Red on hover for close
        
        self.refresh_btn = tk.Label(self.header, text="↻", bg=HEADER_COLOR, fg=TEXT_MUTED, font=("Segoe UI", 12), cursor="hand2")
        self.refresh_btn.pack(side=tk.RIGHT, padx=5)
        self.refresh_btn.bind("<Button-1>", lambda e: self.trigger_refresh())
        self._bind_hover(self.refresh_btn, TEXT_MUTED, TEXT_FG)
        
        # Last updated timestamp (shown after first fetch)
        self.last_updated_label = tk.Label(self.header, text="", bg=HEADER_COLOR, fg=TEXT_MUTED, font=("Segoe UI", 7))
        self.last_updated_label.pack(side=tk.RIGHT, padx=5)
        
        self.content = tk.Frame(self.main_frame, bg=BG_COLOR, padx=10, pady=5)
        self.content.pack(fill=tk.BOTH, expand=True)
        
        # Container for Arcs to keep height constant
        self.arcs_container = tk.Frame(self.content, bg=BG_COLOR)
        self.arcs_container.pack(fill=tk.X)
        
        # Top Arcs (5hr limits)
        self.top_arcs_frame = tk.Frame(self.arcs_container, bg=BG_COLOR)
        self.top_arcs_frame.pack(fill=tk.X)
        
        self.gemini_5h_gauge = ArcGauge(self.top_arcs_frame, size=150, title="Gemini\n(5h)",     color=COLOR_GEMINI,        glow_color=COLOR_GEMINI_GLOW)
        self.gemini_5h_gauge.pack(side=tk.LEFT, padx=5)
        
        self.ext_5h_gauge = ArcGauge(self.top_arcs_frame, size=150, title="External\n(5h)",   color=COLOR_EXT,           glow_color=COLOR_EXT_GLOW)
        self.ext_5h_gauge.pack(side=tk.RIGHT, padx=5)
        
        # Bottom Arcs (Weekly limits) - Hidden by default
        self.weekly_arcs_frame = tk.Frame(self.arcs_container, bg=BG_COLOR)
        
        self.gemini_w_gauge = ArcGauge(self.weekly_arcs_frame, size=150, title="Gemini\n(Weekly)", color=COLOR_GEMINI_WEEKLY, glow_color=COLOR_GEMINI_GLOW)
        self.gemini_w_gauge.pack(side=tk.LEFT, padx=5)
        
        self.ext_w_gauge = ArcGauge(self.weekly_arcs_frame, size=150, title="External\n(Weekly)", color=COLOR_EXT_WEEKLY,    glow_color=COLOR_EXT_GLOW)
        self.ext_w_gauge.pack(side=tk.RIGHT, padx=5)
        
        # Segmented Control Toggle
        self.toggle_frame = tk.Frame(self.content, bg=BG_COLOR)
        self.toggle_frame.pack(pady=4)
        
        # Pill container
        self.toggle_container = tk.Frame(self.toggle_frame, bg="#1E1E1E", padx=2, pady=2, bd=0)
        self.toggle_container.pack()

        seg_font = ("Segoe UI", 8, "bold")
        
        self.btn_5h = tk.Label(self.toggle_container, text=" 5-Hour ", font=seg_font, bg="#333639", fg=TEXT_FG, cursor="hand2", padx=12, pady=2)
        self.btn_5h.pack(side=tk.LEFT)
        self.btn_5h.bind("<Button-1>", lambda e: self.set_view(False))
        
        self.btn_weekly = tk.Label(self.toggle_container, text=" Weekly ", font=seg_font, bg="#1E1E1E", fg=TEXT_MUTED, cursor="hand2", padx=12, pady=2)
        self.btn_weekly.pack(side=tk.LEFT)
        self.btn_weekly.bind("<Button-1>", lambda e: self.set_view(True))
        
        self.show_weekly = False
        
        # History Chart Container
        self.chart_frame = tk.Frame(self.content, bg=SURFACE_COLOR, bd=0, highlightthickness=1, highlightbackground="#2A2B2E", highlightcolor="#2A2B2E")
        self.chart_frame.pack(fill=tk.X, pady=(8, 0), padx=5)
        
        self.chart = HistoryChart(self.chart_frame, width=310, height=95)
        self.chart.pack(padx=2, pady=2)
        
        # Render history chart immediately on boot using local file
        history = history_logger.get_history(minutes=360)
        self.chart.render(history)
        
        # Fixed height
        self.root.geometry(f"{self.width}x{self.base_height}")

    def _bind_hover(self, widget, normal_color, hover_color):
        """Bind hover highlight to any tk.Label button."""
        widget.bind("<Enter>", lambda e: widget.config(fg=hover_color))
        widget.bind("<Leave>", lambda e: widget.config(fg=normal_color))

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
        if self.show_weekly == show_weekly:
            return
            
        self.show_weekly = show_weekly
        if self.show_weekly:
            self.btn_5h.config(bg="#1E1E1E", fg=TEXT_MUTED)
            self.btn_weekly.config(bg="#333639", fg=TEXT_FG)
            self.top_arcs_frame.pack_forget()
            self.weekly_arcs_frame.pack(fill=tk.X)
        else:
            self.btn_weekly.config(bg="#1E1E1E", fg=TEXT_MUTED)
            self.btn_5h.config(bg="#333639", fg=TEXT_FG)
            self.weekly_arcs_frame.pack_forget()
            self.top_arcs_frame.pack(fill=tk.X)

    def create_tray_icon(self):
        try:
            # os is already imported at the top of the module
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.jpg")
            return Image.open(icon_path)
        except Exception:
            # Fallback to drawn icon if file is missing
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
        self.icon = pystray.Icon("AGYMonitor", self.create_tray_icon(), "AGY Fuel Gauge", menu)
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
        # Always show fresh data when user opens the widget
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
        # Loading feedback: brighten the refresh button while fetching
        self.root.after(0, lambda: self.refresh_btn.config(fg=COLOR_GEMINI))
        try:
            data = data_fetcher.fetch_usage_data()
            self.root.after(0, self.update_ui_with_data, data)
        except Exception as e:
            print(f"[AGY Fuel Gauge] Fetch failed: {e}")
        finally:
            self.is_fetching = False
            # Restore refresh button color
            self.root.after(0, lambda: self.refresh_btn.config(fg=TEXT_MUTED))
            
    def update_ui_with_data(self, data):
        g = data.get("gemini", {})
        e = data.get("external", {})
        
        self.gemini_5h_gauge.set_value(g.get("5hr_percent", 0), g.get("reset_time_5h", "--"))
        self.ext_5h_gauge.set_value(e.get("5hr_percent", 0), e.get("reset_time_5h", "--"))
        
        self.gemini_w_gauge.set_value(g.get("weekly_percent", 0), g.get("reset_time_weekly", "--"))
        self.ext_w_gauge.set_value(e.get("weekly_percent", 0), e.get("reset_time_weekly", "--"))
        
        # Update last-updated timestamp in header
        now_str = datetime.now().strftime("%H:%M")
        self.last_updated_label.config(text=now_str)
        
        # Render history chart
        history = history_logger.get_history(minutes=360)  # Last 6 hours
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
