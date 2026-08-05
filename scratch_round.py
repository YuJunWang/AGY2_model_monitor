import tkinter as tk
import ctypes

root = tk.Tk()
root.geometry("200x200")
root.overrideredirect(True)
root.attributes("-alpha", 0.8)
root.config(bg="red")

def set_rounded():
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    DWMWA_WINDOW_CORNER_PREFERENCE = 33
    DWMWCP_ROUND = 2
    value = ctypes.c_int(DWMWCP_ROUND)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(value), ctypes.sizeof(value))

root.after(100, set_rounded)
tk.Button(root, text="Exit", command=root.destroy).pack(expand=True)
root.mainloop()
