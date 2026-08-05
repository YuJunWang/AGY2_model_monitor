import tkinter as tk
import ctypes

root = tk.Tk()
root.geometry("134x500")
root.overrideredirect(True)
root.attributes('-alpha', 0.82)
root.config(bg="#12141A")

def apply_region():
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    
    # Create main body region
    hRgnMain = ctypes.windll.gdi32.CreateRoundRectRgn(24, 0, 134, 500, 16, 16)
    
    # Create tab region
    hRgnTab = ctypes.windll.gdi32.CreateRoundRectRgn(0, 30, 40, 170, 16, 16) # Overlap into main
    
    # Combine regions
    RGN_OR = 2
    hRgnCombined = ctypes.windll.gdi32.CreateRectRgn(0, 0, 0, 0)
    ctypes.windll.gdi32.CombineRgn(hRgnCombined, hRgnMain, hRgnTab, RGN_OR)
    
    # Set window region
    ctypes.windll.user32.SetWindowRgn(hwnd, hRgnCombined, True)

root.after(100, apply_region)

tk.Button(root, text="Exit", command=root.destroy).place(x=30, y=200)
root.mainloop()
