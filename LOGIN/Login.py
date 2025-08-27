import time
import json
import os

USER_DATA_FILE = "user_data.json"
LOGIN_ATTEMPTS_FILE = "login_attempts.json"
LOCKOUT_DURATION = 30  # Lockout duration in seconds

def load_user_data():
    """Loads user data from the JSON file."""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    else:
        return {}

def save_user_data(user_data):
    """Saves user data to the JSON file."""
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=4)

def load_login_attempts():
    """Loads login attempt data from the JSON file."""
    if os.path.exists(LOGIN_ATTEMPTS_FILE):
        with open(LOGIN_ATTEMPTS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    else:
        return {}

def save_login_attempts(login_attempts):
    """Saves login attempt data to the JSON file."""
    with open(LOGIN_ATTEMPTS_FILE, "w") as f:
        json.dump(login_attempts, f, indent=4)

def register_user(username, password):
    """Registers a new user."""
    user_data = load_user_data()
    if username in user_data:
        print("Username already exists.")
        return False
    user_data[username] = {"password": password}
    save_user_data(user_data)
    print("User registered successfully.")
    return True

def login(username, password):
    """Logs in a user, with lockout functionality."""

    login_attempts = load_login_attempts()
    current_time = time.time()

    if username in login_attempts and login_attempts[username]["locked_until"] > current_time:
        remaining_time = login_attempts[username]["locked_until"] - current_time
        print(f"Account locked. Try again in {remaining_time:.0f} seconds.")
        return False

    user_data = load_user_data()
    if username in user_data and user_data[username]["password"] == password:
        if username in login_attempts:
            del login_attempts[username] #clear lockout data on successful login
            save_login_attempts(login_attempts)
        print("Login successful.")
        return True
    else:
        if username not in login_attempts:
            login_attempts[username] = {"failed_attempts": 0, "locked_until": 0}
        login_attempts[username]["failed_attempts"] += 1
        login_attempts[username]["locked_until"] = current_time + LOCKOUT_DURATION
        save_login_attempts(login_attempts)
        print("Login failed.")
        return False

def main():
    while True:
        print("\nLogin Platform")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            username = input("Enter username: ")
            password = input("Enter password: ")
            register_user(username, password)

        elif choice == "2":
            username = input("Enter username: ")
            password = input("Enter password: ")
            login(username, password)

        elif choice == "3":
            break

        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()