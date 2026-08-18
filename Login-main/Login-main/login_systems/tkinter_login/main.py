"""
Tkinter GUI Login Authentication System
Features: Registration, Login, Password Reset, SQLite Database, Password Hashing
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import hashlib
import secrets
import re
from datetime import datetime


class Database:
    """SQLite database handler for user management."""

    def __init__(self, db_file="users.db"):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_file)

    def init_db(self):
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                reset_token TEXT,
                reset_token_expiry TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                success INTEGER DEFAULT 1
            )
        """)

        conn.commit()
        conn.close()

    def hash_password(self, password, salt=None):
        """Hash password with PBKDF2."""
        if salt is None:
            salt = secrets.token_hex(32)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return salt + pwdhash.hex()

    def verify_password(self, stored_password, provided_password):
        """Verify a password against its hash."""
        salt = stored_password[:64]
        return stored_password == self.hash_password(provided_password, salt)

    def register_user(self, username, email, password):
        """Register a new user."""
        if not self.validate_password(password):
            return False, "Password must be at least 8 chars with uppercase, lowercase, digit, and special char."

        if not self.validate_email(email):
            return False, "Invalid email format."

        password_hash = self.hash_password(password)

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            conn.commit()
            return True, "Registration successful!"
        except sqlite3.IntegrityError:
            return False, "Username or email already exists."
        finally:
            conn.close()

    def authenticate_user(self, username, password):
        """Authenticate user credentials."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash, is_active FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        conn.close()

        if not result:
            return False, "User not found."

        stored_hash, is_active = result
        if not is_active:
            return False, "Account is deactivated."

        if self.verify_password(stored_hash, password):
            self.update_last_login(username)
            self.log_login(username, success=1)
            return True, "Login successful!"
        else:
            self.log_login(username, success=0)
            return False, "Incorrect password."

    def update_last_login(self, username):
        """Update last login timestamp."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?",
            (username,)
        )
        conn.commit()
        conn.close()

    def log_login(self, username, success=1):
        """Log login attempt."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO login_history (username, success) VALUES (?, ?)",
            (username, success)
        )
        conn.commit()
        conn.close()

    def generate_reset_token(self, email):
        """Generate password reset token."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return False, "Email not found."

        token = secrets.token_urlsafe(32)
        cursor.execute(
            """UPDATE users 
               SET reset_token = ?, reset_token_expiry = datetime('now', '+1 hour') 
               WHERE email = ?""",
            (token, email)
        )
        conn.commit()
        conn.close()
        return True, token

    def reset_password(self, token, new_password):
        """Reset password using token."""
        if not self.validate_password(new_password):
            return False, "Password does not meet requirements."

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT email FROM users 
               WHERE reset_token = ? AND reset_token_expiry > datetime('now')""",
            (token,)
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            return False, "Invalid or expired token."

        password_hash = self.hash_password(new_password)
        cursor.execute(
            """UPDATE users 
               SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL 
               WHERE reset_token = ?""",
            (password_hash, token)
        )
        conn.commit()
        conn.close()
        return True, "Password reset successful!"

    def validate_password(self, password):
        """Validate password strength."""
        if len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"\d", password):
            return False
        if not re.search(r'[!@#$%^&*(),\.?":{}|<>]', password):
            return False
        return True

    def validate_email(self, email):
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def get_user_info(self, username):
        """Get user information."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, email, created_at, last_login FROM users WHERE username = ?",
            (username,)
        )
        result = cursor.fetchone()
        conn.close()
        return result

    def get_login_history(self, username):
        """Get login history for user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT login_time, success FROM login_history WHERE username = ? ORDER BY login_time DESC LIMIT 10",
            (username,)
        )
        results = cursor.fetchall()
        conn.close()
        return results


class LoginApp:
    """Main Tkinter Application."""

    def __init__(self, root):
        self.root = root
        self.root.title("Secure Login System")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        # Center window on screen
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')

        self.db = Database()
        self.current_user = None

        self.setup_styles()
        self.show_login_screen()

    def setup_styles(self):
        """Configure ttk styles."""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background="#1e1e2e")
        self.style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4", font=("Helvetica", 11))
        self.style.configure("Header.TLabel", font=("Helvetica", 24, "bold"), foreground="#89b4fa")
        self.style.configure("TButton", font=("Helvetica", 11), padding=10)
        self.style.configure("Primary.TButton", background="#89b4fa", foreground="#1e1e2e")
        self.style.configure("Secondary.TButton", background="#313244", foreground="#cdd6f4")
        self.style.configure("Danger.TButton", background="#f38ba8", foreground="#1e1e2e")

    def clear_frame(self):
        """Clear all widgets from root."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_entry(self, parent, placeholder, show=None, width=35):
        """Create a styled entry field."""
        entry = tk.Entry(parent, width=width, font=("Helvetica", 12), 
                        bg="#313244", fg="#6c7086", insertbackground="#cdd6f4",
                        relief="flat", bd=8)
        entry.insert(0, placeholder)
        entry._show_char = show
        entry.bind('<FocusIn>', lambda e: self.on_entry_focus_in(e, placeholder))
        entry.bind('<FocusOut>', lambda e: self.on_entry_focus_out(e, placeholder))
        return entry

    def on_entry_focus_in(self, event, placeholder):
        if event.widget.get() == placeholder:
            event.widget.delete(0, tk.END)
            event.widget.config(fg="#cdd6f4")
        if hasattr(event.widget, '_show_char') and event.widget._show_char:
            event.widget.config(show=event.widget._show_char)

    def on_entry_focus_out(self, event, placeholder):
        if event.widget.get() == "":
            event.widget.insert(0, placeholder)
            event.widget.config(fg="#6c7086")
            event.widget.config(show="")

    def show_login_screen(self):
        """Display the login screen."""
        self.clear_frame()

        frame = ttk.Frame(self.root, padding="40")
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="🔐 Secure Login", style="Header.TLabel").pack(pady=(0, 30))

        self.login_username = self.create_entry(frame, "Username")
        self.login_username.pack(pady=10, ipady=5)

        self.login_password = self.create_entry(frame, "Password", show="●")
        self.login_password.pack(pady=10, ipady=5)

        ttk.Button(frame, text="Login", command=self.handle_login, style="Primary.TButton").pack(pady=20, fill="x")

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Create Account", command=self.show_register_screen, 
                  style="Secondary.TButton").pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Forgot Password?", command=self.show_forgot_screen,
                  style="Secondary.TButton").pack(side="left", padx=5)

    def show_register_screen(self):
        """Display the registration screen."""
        self.clear_frame()

        frame = ttk.Frame(self.root, padding="40")
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="📝 Create Account", style="Header.TLabel").pack(pady=(0, 30))

        self.reg_username = self.create_entry(frame, "Username")
        self.reg_username.pack(pady=8, ipady=5)

        self.reg_email = self.create_entry(frame, "Email")
        self.reg_email.pack(pady=8, ipady=5)

        self.reg_password = self.create_entry(frame, "Password", show="●")
        self.reg_password.pack(pady=8, ipady=5)

        self.reg_confirm = self.create_entry(frame, "Confirm Password", show="●")
        self.reg_confirm.pack(pady=8, ipady=5)

        ttk.Label(frame, text="ℹ️ Password: 8+ chars, A-Z, a-z, 0-9, special char", 
                 font=("Helvetica", 9), foreground="#6c7086").pack(pady=5)

        ttk.Button(frame, text="Register", command=self.handle_register, 
                  style="Primary.TButton").pack(pady=20, fill="x")
        ttk.Button(frame, text="Back to Login", command=self.show_login_screen,
                  style="Secondary.TButton").pack(fill="x")

    def show_forgot_screen(self):
        """Display password reset request screen."""
        self.clear_frame()

        frame = ttk.Frame(self.root, padding="40")
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text="🔑 Reset Password", style="Header.TLabel").pack(pady=(0, 30))

        ttk.Label(frame, text="Enter your email to receive a reset token:", 
                 wraplength=400).pack(pady=10)

        self.forgot_email = self.create_entry(frame, "Email")
        self.forgot_email.pack(pady=15, ipady=5)

        ttk.Button(frame, text="Generate Token", command=self.handle_forgot, 
                  style="Primary.TButton").pack(pady=20, fill="x")

        ttk.Label(frame, text="Or enter token directly:", wraplength=400).pack(pady=10)

        self.reset_token = self.create_entry(frame, "Reset Token")
        self.reset_token.pack(pady=8, ipady=5)

        self.new_password = self.create_entry(frame, "New Password", show="●")
        self.new_password.pack(pady=8, ipady=5)

        ttk.Button(frame, text="Reset with Token", command=self.handle_reset, 
                  style="Primary.TButton").pack(pady=10, fill="x")
        ttk.Button(frame, text="Back to Login", command=self.show_login_screen,
                  style="Secondary.TButton").pack(fill="x")

    def show_dashboard(self, username):
        """Display user dashboard after login."""
        self.clear_frame()
        self.current_user = username

        frame = ttk.Frame(self.root, padding="30")
        frame.pack(expand=True, fill="both")

        ttk.Label(frame, text=f"👋 Welcome, {username}!", style="Header.TLabel").pack(pady=(0, 20))

        # User info
        info = self.db.get_user_info(username)
        if info:
            info_frame = tk.Frame(frame, bg="#313244", padx=20, pady=15)
            info_frame.pack(fill="x", pady=10)

            tk.Label(info_frame, text=f"📧 Email: {info[1]}", 
                    bg="#313244", fg="#cdd6f4", font=("Helvetica", 11)).pack(anchor="w")
            tk.Label(info_frame, text=f"📅 Member since: {info[2]}", 
                    bg="#313244", fg="#cdd6f4", font=("Helvetica", 11)).pack(anchor="w")
            tk.Label(info_frame, text=f"🕐 Last login: {info[3] or 'Never'}", 
                    bg="#313244", fg="#cdd6f4", font=("Helvetica", 11)).pack(anchor="w")

        # Login history
        history = self.db.get_login_history(username)
        if history:
            hist_frame = tk.Frame(frame, bg="#1e1e2e")
            hist_frame.pack(fill="x", pady=10)

            ttk.Label(hist_frame, text="📊 Recent Login Activity:", 
                     font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 5))

            for time, success in history[:5]:
                status = "✅ Success" if success else "❌ Failed"
                tk.Label(hist_frame, text=f"  {time} — {status}", 
                        bg="#1e1e2e", fg="#a6e3a1" if success else "#f38ba8", 
                        font=("Helvetica", 10)).pack(anchor="w")

        ttk.Button(frame, text="Logout", command=self.handle_logout, 
                  style="Danger.TButton").pack(pady=30, fill="x")

    def handle_login(self):
        """Process login attempt."""
        username = self.login_username.get()
        password = self.login_password.get()

        if username in ["Username", ""] or password in ["Password", ""]:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        success, msg = self.db.authenticate_user(username, password)
        if success:
            messagebox.showinfo("Success", msg)
            self.show_dashboard(username)
        else:
            messagebox.showerror("Error", msg)

    def handle_register(self):
        """Process registration."""
        username = self.reg_username.get()
        email = self.reg_email.get()
        password = self.reg_password.get()
        confirm = self.reg_confirm.get()

        if any(v in ["", placeholder.split()[0]] for v, placeholder in [
            (username, "Username"), (email, "Email"), (password, "Password"), (confirm, "Confirm")
        ]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        success, msg = self.db.register_user(username, email, password)
        if success:
            messagebox.showinfo("Success", msg)
            self.show_login_screen()
        else:
            messagebox.showerror("Error", msg)

    def handle_forgot(self):
        """Process forgot password request."""
        email = self.forgot_email.get()
        if email in ["", "Email"]:
            messagebox.showerror("Error", "Please enter your email.")
            return

        success, result = self.db.generate_reset_token(email)
        if success:
            messagebox.showinfo("Token Generated", 
                f"Your reset token is:\n\n{result}\n\n(In production, this would be emailed to you.)")
        else:
            messagebox.showerror("Error", result)

    def handle_reset(self):
        """Process password reset."""
        token = self.reset_token.get()
        new_pass = self.new_password.get()

        if token in ["", "Reset Token"] or new_pass in ["", "New Password"]:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        success, msg = self.db.reset_password(token, new_pass)
        if success:
            messagebox.showinfo("Success", msg)
            self.show_login_screen()
        else:
            messagebox.showerror("Error", msg)

    def handle_logout(self):
        """Log out current user."""
        self.current_user = None
        self.show_login_screen()


def main():
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
