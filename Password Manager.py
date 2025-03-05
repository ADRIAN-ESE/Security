import json
import os
from cryptography.fernet import Fernet


# Generate or load encryption key
def load_key():
    """Load the encryption key from a file or generate a new one if not present."""
    key_file_path = "key.key"
    if not os.path.exists(key_file_path):
        print("Encryption key not found. Generating a new one...")
        key = Fernet.generate_key()
        with open(key_file_path, "wb") as key_file:
            key_file.write(key)
        print("New encryption key generated and saved.")
    else:
        with open(key_file_path, "rb") as key_file:
            key = key_file.read()
    return key


# Encrypt and decrypt functions
def encrypt(data, key):
    """Encrypt data using the given key."""
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()


def decrypt(data, key):
    """Decrypt data using the given key."""
    f = Fernet(key)
    return f.decrypt(data.encode()).decode()


# File handling for saving and loading passwords
def save_passwords(passwords):
    """Save passwords dictionary to a JSON file."""
    try:
        with open("passwords.json", "w") as file:
            json.dump(passwords, file, indent=4)
    except IOError as e:
        print(f"Error saving passwords: {e}")


def load_passwords():
    """Load passwords from the JSON file."""
    if os.path.exists("passwords.json"):
        try:
            with open("passwords.json", "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Error reading password file. It may be corrupted.")
            return {}
    return {}


# Main password manager logic
def add_password(service, username, password, key):
    """Add a new password for a service."""
    passwords = load_passwords()
    if service in passwords:
        print(f"Service '{service}' already exists. Overwriting...")
    passwords[service] = {
        "username": username,
        "password": encrypt(password, key)
    }
    save_passwords(passwords)
    print(f"Password for '{service}' added successfully.")


def retrieve_password(service, key):
    """Retrieve the password for a given service."""
    passwords = load_passwords()
    if service in passwords:
        encrypted_password = passwords[service]["password"]
        username = passwords[service]["username"]
        password = decrypt(encrypted_password, key)
        print(f"Service: {service}\nUsername: {username}\nPassword: {password}")
    else:
        print(f"Service '{service}' not found.")


def list_services():
    """List all stored services."""
    passwords = load_passwords()
    if passwords:
        print("Stored services:")
        for service in passwords:
            print(f"- {service}")
    else:
        print("No passwords stored.")


def reset_passwords():
    """Reset (delete) all stored passwords by removing the passwords.json file."""
    if os.path.exists("passwords.json"):
        os.remove("passwords.json")
        print("All saved services have been reset (deleted).")
    else:
        print("No saved services to reset.")


# User interface
def main():
    """Main function for password manager interaction."""
    key = load_key()
    print("Welcome to the Password Manager!")

    while True:
        print("\nOptions:")
        print("1. Add a password")
        print("2. Retrieve a password")
        print("3. List all services")
        print("4. Reset all saved services")
        print("5. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            service = input("Enter the service name: ").strip()
            username = input("Enter the username: ").strip()
            password = input("Enter the password: ").strip()
            add_password(service, username, password, key)
        elif choice == "2":
            service = input("Enter the service name: ").strip()
            retrieve_password(service, key)
        elif choice == "3":
            list_services()
        elif choice == "4":
            reset_passwords()  # Reset the saved services
        elif choice == "5":
            print("Exiting Password Manager.")
            break
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
