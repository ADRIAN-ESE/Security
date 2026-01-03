import json
import os
import time
import hashlib
import secrets
from tempfile import NamedTemporaryFile
import shutil

USER_DATA_FILE = "user_data.json"
LOGIN_ATTEMPTS_FILE = "login_attempts.json"

MAX_ATTEMPTS = 5
LOCKOUT_DURATION = 30  # seconds


# ---------- Utility Functions ----------

def load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def atomic_save(path, data):
    with NamedTemporaryFile("w", delete=False) as temp:
        json.dump(data, temp, indent=4)
        temp_name = temp.name
    shutil.move(temp_name, path)


# ---------- Password Handling ----------

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100_000
    ).hex()
    return f"{salt}${hashed}"


def verify_password(stored_hash, password):
    salt, hashed = stored_hash.split("$")
    return hash_password(password, salt) == stored_hash


# ---------- Core Logic ----------

def register_user(username, password):
    users = load_json(USER_DATA_FILE)

    if username in users:
        print("Username already exists.")
        return False

    users[username] = {
        "password": hash_password(password),
        "created_at": time.time()
    }

    atomic_save(USER_DATA_FILE, users)
    print("User registered successfully.")
    return True


def login(username, password):
    users = load_json(USER_DATA_FILE)
    attempts = load_json(LOGIN_ATTEMPTS_FILE)
    now = time.time()

    record = attempts.get(username, {"fails": 0, "locked_until": 0})

    if record["locked_until"] > now:
        remaining = int(record["locked_until"] - now)
        print(f"Account locked. Try again in {remaining}s.")
        return False

    if username in users and verify_password(users[username]["password"], password):
        attempts.pop(username, None)
        atomic_save(LOGIN_ATTEMPTS_FILE, attempts)
        print("Login successful.")
        return True

    # Failed login
    record["fails"] += 1

    if record["fails"] >= MAX_ATTEMPTS:
        record["locked_until"] = now + LOCKOUT_DURATION
        print("Too many attempts. Account locked.")
    else:
        print(f"Login failed ({record['fails']}/{MAX_ATTEMPTS}).")

    attempts[username] = record
    atomic_save(LOGIN_ATTEMPTS_FILE, attempts)
    return False


# ---------- CLI ----------

def main():
    while True:
        print("\nLogin Platform")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Choice: ").strip()

        if choice == "1":
            register_user(
                input("Username: "),
                input("Password: ")
            )

        elif choice == "2":
            login(
                input("Username: "),
                input("Password: ")
            )

        elif choice == "3":
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
