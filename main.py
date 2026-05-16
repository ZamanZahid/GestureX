import tkinter as tk
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(__file__)

HAND_CONTROL_SCRIPT = os.path.join(BASE_DIR, "hand_control_mac.py")
KEYBOARD_CONTROL_SCRIPT = os.path.join(BASE_DIR, "keyboard_control_mac.py")
EYE_CONTROL_SCRIPT = os.path.join(BASE_DIR, "eye_control_mac.py")

def open_mouse():
    subprocess.Popen([sys.executable, HAND_CONTROL_SCRIPT])

def open_keyboard():
    subprocess.Popen([sys.executable, KEYBOARD_CONTROL_SCRIPT])

def open_eye():
    subprocess.Popen([sys.executable, EYE_CONTROL_SCRIPT])

root = tk.Tk()
root.title("Gesture Control Hub")
root.geometry("360x270")
root.configure(bg="#050301")

window_width = 360
window_height = 270

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

pos_x = (screen_width // 2) - (window_width // 2)
pos_y = (screen_height // 2) - (window_height // 2)

root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

# ========================
# Button Styling
# ========================

def make_button(text, command):

    btn = tk.Button(
        root,
        text=text,
        font=("Trebuchet MS", 14, "bold"),
        bg="#F5D061",
        fg="#050301",
        activebackground="#d9b84f",
        activeforeground="#ffffff",
        relief="flat",
        width=20,
        height=2,
        command=command
    )

    btn.pack(pady=8)

    def on_enter(e):
        btn.config(bg="#d9b84f")

    def on_leave(e):
        btn.config(bg="#F5D061")

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

# spacing
tk.Label(root, text="", bg="#050301").pack(pady=4)


make_button("Open Hand Keyboard", open_keyboard)
make_button("Open Hand Mouse", open_mouse)
make_button("Open Eye Mouse", open_eye)

# Footer
footer_label = tk.Label(
    root,
    text="Made By: Zaman Zahid ❤️",
    font=("Trebuchet MS", 12, "bold"),
    bg="#050301",
    fg="#F5D061"
)

footer_label.pack(side="bottom", pady=10)

root.mainloop()