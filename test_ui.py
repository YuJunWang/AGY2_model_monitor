import tkinter as tk
import math

class ArcGauge(tk.Canvas):
    def __init__(self, parent, size=120, title="Gemini 5hr", color="#4FC3F7", **kwargs):
        super().__init__(parent, width=size, height=size, bg="#1E1E1E", highlightthickness=0, **kwargs)
        self.size = size
        self.color = color
        self.title = title
        self.arc_width = size * 0.12
        
        # Draw background arc
        pad = self.arc_width
        self.bbox = (pad, pad, size - pad, size - pad)
        
        # bg arc (extent 180 means from 3 o'clock counter-clockwise to 9 o'clock)
        # To draw a top half circle: start=0, extent=180
        self.create_arc(*self.bbox, start=0, extent=180, style=tk.ARC, width=self.arc_width, outline="#333333")
        
        # fg arc
        self.fg_arc = self.create_arc(*self.bbox, start=180, extent=0, style=tk.ARC, width=self.arc_width, outline=self.color)
        
        # Text elements
        self.pct_text = self.create_text(size/2, size/2 - 15, text="0%", fill="white", font=("Segoe UI", 16, "bold"))
        self.time_text = self.create_text(size/2, size/2 + 5, text="--h --m", fill="#AAAAAA", font=("Segoe UI", 9))
        self.title_text = self.create_text(size/2, size/2 + 25, text=title, fill="#E0E0E0", font=("Segoe UI", 9, "bold"))

    def set_value(self, pct, reset_time):
        # pct is 0-100 remaining
        # Extent goes negative (clockwise from 180)
        extent = -(180 * (pct / 100))
        self.itemconfig(self.fg_arc, extent=extent)
        self.itemconfig(self.pct_text, text=f"{int(pct)}%")
        self.itemconfig(self.time_text, text=reset_time)


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="#1E1E1E")
    
    gauge = ArcGauge(root, size=150, title="Gemini 3 Flash", color="#4FC3F7")
    gauge.pack(padx=20, pady=20)
    gauge.set_value(78, "3h 57m")
    
    root.mainloop()
