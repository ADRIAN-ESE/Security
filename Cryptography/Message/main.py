import tkinter as tk
from tkinter import filedialog, messagebox
import pyperclip
from crypto_utils import encrypt_message, decrypt_message, encrypt_file, decrypt_file

# -----------------------------
# Functions
# -----------------------------
def encrypt_text():
    msg = txt_message.get("1.0", tk.END).strip()
    pwd = entry_password.get().strip()
    if not msg or not pwd:
        messagebox.showerror("Error", "Enter message and password!")
        return
    encrypted = encrypt_message(msg, pwd)
    txt_result.delete("1.0", tk.END)
    txt_result.insert(tk.END, encrypted)

def decrypt_text():
    encrypted = txt_message.get("1.0", tk.END).strip()
    pwd = entry_password.get().strip()
    if not encrypted or not pwd:
        messagebox.showerror("Error", "Enter encrypted message and password!")
        return
    decrypted = decrypt_message(encrypted, pwd)
    txt_result.delete("1.0", tk.END)
    txt_result.insert(tk.END, decrypted)

def copy_result():
    result = txt_result.get("1.0", tk.END).strip()
    if result:
        pyperclip.copy(result)
        messagebox.showinfo("Copied", "Result copied to clipboard!")

def encrypt_file_btn():
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if not file_path:
        return
    pwd = entry_password.get().strip()
    if not pwd:
        messagebox.showerror("Error", "Enter a password!")
        return
    out_file = encrypt_file(file_path, pwd)
    messagebox.showinfo("Success", f"Encrypted file created:\n{out_file}")

def decrypt_file_btn():
    file_path = filedialog.askopenfilename(filetypes=[("Encrypted Files", "*.enc")])
    if not file_path:
        return
    pwd = entry_password.get().strip()
    if not pwd:
        messagebox.showerror("Error", "Enter a password!")
        return
    out_file = decrypt_file(file_path, pwd)
    messagebox.showinfo("Success", f"Decrypted file created:\n{out_file}")

# -----------------------------
# GUI Setup
# -----------------------------
root = tk.Tk()
root.title("Message Encryptor - Portfolio Version")
root.geometry("600x450")

# Message input
tk.Label(root, text="Message / Encrypted Text:").pack(padx=10, pady=5)
txt_message = tk.Text(root, height=5, width=70)
txt_message.pack(padx=10, pady=5)

# Password
tk.Label(root, text="Password:").pack(padx=10, pady=5)
entry_password = tk.Entry(root, show="*", width=40)
entry_password.pack(padx=10, pady=5)

# Buttons
frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=10)

tk.Button(frame_buttons, text="Encrypt Text", command=encrypt_text, bg="green", fg="white", width=15).grid(row=0, column=0, padx=5)
tk.Button(frame_buttons, text="Decrypt Text", command=decrypt_text, bg="blue", fg="white", width=15).grid(row=0, column=1, padx=5)
tk.Button(frame_buttons, text="Copy Result", command=copy_result, bg="orange", fg="white", width=15).grid(row=0, column=2, padx=5)
tk.Button(frame_buttons, text="Encrypt File", command=encrypt_file_btn, bg="purple", fg="white", width=15).grid(row=1, column=0, padx=5, pady=5)
tk.Button(frame_buttons, text="Decrypt File", command=decrypt_file_btn, bg="brown", fg="white", width=15).grid(row=1, column=1, padx=5, pady=5)

# Result box
tk.Label(root, text="Result:").pack(padx=10, pady=5)
txt_result = tk.Text(root, height=7, width=70)
txt_result.pack(padx=10, pady=5)

root.mainloop()
