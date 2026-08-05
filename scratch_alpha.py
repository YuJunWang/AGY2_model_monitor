import tkinter as tk

root = tk.Tk()
root.geometry("200x200")
root.attributes('-topmost', True)
root.overrideredirect(True)
root.attributes('-alpha', 0.8)
root.attributes('-transparentcolor', '#000001')
root.config(bg='#000001')

f = tk.Frame(root, bg='red', width=100, height=100)
f.place(x=50, y=50)

tk.Button(f, text="Exit", command=root.destroy).pack(expand=True)
root.mainloop()
