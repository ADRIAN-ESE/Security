import tkinter as tk
from tkinter import messagebox, scrolledtext
import base64

# ----------------- Encryption / Decryption Logic -----------------

def caesar_cipher(text, shift, decrypt=False):
    result = ""
    if decrypt:
        shift = -shift
    for char in text:
        if char.isalpha():
            shift_base = 65 if char.isupper() else 97
            result += chr((ord(char) - shift_base + shift) % 26 + shift_base)
        else:
            result += char
    return result

def xor_cipher(text, key):
    return ''.join(chr(ord(c) ^ key) for c in text)

def base64_encrypt(text):
    return base64.b64encode(text.encode()).decode()

def base64_decrypt(text):
    try:
        return base64.b64decode(text.encode()).decode()
    except Exception:
        return "[Invalid Base64 Input]"

# ----------------- GUI Application -----------------

class EncryptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Encryption & Decryption Tool")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        # Create canvas for gradient background
        self.canvas = tk.Canvas(self.root, width=800, height=600, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.draw_gradient(self.canvas, 800, 600)

        # UI Frame (foreground)
        self.frame = tk.Frame(self.canvas, bg="#1e1e2f")
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        self.title_label = tk.Label(
            self.frame,
            text="🔒 Encryption & Decryption Tool 🔑",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#1e1e2f"
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=15)

        # Input text
        self.input_text = scrolledtext.ScrolledText(
            self.frame, wrap=tk.WORD, width=60, height=10, font=("Consolas", 11)
        )
        self.input_text.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        # Dropdown for method selection
        self.method_var = tk.StringVar(value="Caesar Cipher")
        self.method_menu = tk.OptionMenu(
            self.frame, self.method_var, "Caesar Cipher", "XOR Cipher", "Base64"
        )
        self.method_menu.config(font=("Arial", 12), bg="#2c2c3c", fg="white")
        self.method_menu.grid(row=2, column=0, columnspan=2, pady=10)

        # Key entry
        self.key_label = tk.Label(
            self.frame, text="Key / Shift:", font=("Arial", 12), fg="white", bg="#1e1e2f"
        )
        self.key_label.grid(row=3, column=0, pady=5)
        self.key_entry = tk.Entry(self.frame, font=("Arial", 12), width=15)
        self.key_entry.grid(row=3, column=1, pady=5)

        # Buttons
        self.encrypt_btn = tk.Button(
            self.frame,
            text="Encrypt",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=12,
            command=self.encrypt_text
        )
        self.encrypt_btn.grid(row=4, column=0, pady=10, padx=5)

        self.decrypt_btn = tk.Button(
            self.frame,
            text="Decrypt",
            font=("Arial", 12, "bold"),
            bg="#F44336",
            fg="white",
            width=12,
            command=self.decrypt_text
        )
        self.decrypt_btn.grid(row=4, column=1, pady=10, padx=5)

        # Output box
        self.output_text = scrolledtext.ScrolledText(
            self.frame, wrap=tk.WORD, width=60, height=10, font=("Consolas", 11)
        )
        self.output_text.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    def draw_gradient(self, canvas, width, height, start_color=(30, 30, 30), end_color=(80, 0, 100)):
        """Draws a vertical gradient background with valid hex colors"""
        r1, g1, b1 = start_color
        r2, g2, b2 = end_color

        for i in range(height):
            r = int(r1 + (r2 - r1) * (i / height))
            g = int(g1 + (g2 - g1) * (i / height))
            b = int(b1 + (b2 - b1) * (i / height))
            color = f"#{r:02x}{g:02x}{b:02x}"  # Always valid hex code
            canvas.create_line(0, i, width, i, fill=color)

    def encrypt_text(self):
        text = self.input_text.get("1.0", tk.END).strip()
        method = self.method_var.get()
        key = self.key_entry.get().strip()
        result = ""

        if not text:
            messagebox.showwarning("Warning", "Please enter some text.")
            return

        try:
            if method == "Caesar Cipher":
                shift = int(key) if key else 3
                result = caesar_cipher(text, shift)
            elif method == "XOR Cipher":
                xor_key = int(key) if key else 42
                result = xor_cipher(text, xor_key)
            elif method == "Base64":
                result = base64_encrypt(text)
        except Exception as e:
            result = f"[Error] {e}"

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, result)

    def decrypt_text(self):
        text = self.input_text.get("1.0", tk.END).strip()
        method = self.method_var.get()
        key = self.key_entry.get().strip()
        result = ""

        if not text:
            messagebox.showwarning("Warning", "Please enter some text.")
            return

        try:
            if method == "Caesar Cipher":
                shift = int(key) if key else 3
                result = caesar_cipher(text, shift, decrypt=True)
            elif method == "XOR Cipher":
                xor_key = int(key) if key else 42
                result = xor_cipher(text, xor_key)
            elif method == "Base64":
                result = base64_decrypt(text)
        except Exception as e:
            result = f"[Error] {e}"

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, result)


if __name__ == "__main__":
    root = tk.Tk()
    app = EncryptionApp(root)
    root.mainloop()
