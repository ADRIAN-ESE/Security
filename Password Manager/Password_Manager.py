import json
import os
import secrets
import string

PASSWORD_FILE = "passwords.json"

def load_passwords():
    """Loads passwords from the JSON file."""
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}  # Handle empty or corrupted file
    else:
        return {}

def save_passwords(passwords):
    """Saves passwords to the JSON file."""
    with open(PASSWORD_FILE, "w") as f:
        json.dump(passwords, f, indent=4)

def generate_password(length=12):
    """Generates a secure password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def add_password(site, username, password):
    """Adds a new password to the manager."""
    passwords = load_passwords()
    if site in passwords:
        print(f"Warning: Password for {site} already exists. Overwriting.")

    passwords[site] = {"username": username, "password": password}
    save_passwords(passwords)
    print(f"Password for {site} added successfully.")

def get_password(site):
    """Retrieves a password for a given site."""
    passwords = load_passwords()
    if site in passwords:
        return passwords[site]["username"], passwords[site]["password"]
    else:
        return None, None

def list_sites():
    """Lists all stored sites."""
    passwords = load_passwords()
    if not passwords:
        print("No passwords stored.")
    else:
        print("Stored sites:")
        for site in passwords:
            print(f"- {site}")

def reset_passwords():
    """Resets all stored passwords."""
    if os.path.exists(PASSWORD_FILE):
        os.remove(PASSWORD_FILE)
    print("Password data reset.")

def main():
    while True:
        print("\nPassword Manager")
        print("1. Add Password")
        print("2. Get Password")
        print("3. List Sites")
        print("4. Generate Password")
        print("5. Reset All Passwords")
        print("6. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            site = input("Enter site name: ")
            username = input("Enter username: ")
            password = input("Enter password (or leave blank to generate): ")
            if not password:
                password = generate_password()
                print(f"Generated password: {password}")
            add_password(site, username, password)

        elif choice == "2":
            site = input("Enter site name: ")
            username, password = get_password(site)
            if username and password:
                print(f"Username: {username}")
                print(f"Password: {password}")
            else:
                print(f"Password for {site} not found.")

        elif choice == "3":
            list_sites()

        elif choice == "4":
            length = int(input("Enter password length (default 12): ") or 12)
            print(f"Generated password: {generate_password(length)}")

        elif choice == "5":
            reset_passwords()

        elif choice == "6":
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()