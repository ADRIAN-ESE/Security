import hashlib
import itertools
import os
import time


def hash_password(password, hash_type='md5'):
    """
    Hashes a given password using the specified hash type.
    Supported types: md5, sha1, sha256, sha512.
    """
    try:
        if hash_type == 'md5':
            return hashlib.md5(password.encode()).hexdigest()
        elif hash_type == 'sha1':
            return hashlib.sha1(password.encode()).hexdigest()
        elif hash_type == 'sha256':
            return hashlib.sha256(password.encode()).hexdigest()
        elif hash_type == 'sha512':
            return hashlib.sha512(password.encode()).hexdigest()
        else:
            print(f"Error: Unsupported hash type '{hash_type}'. Supported types: md5, sha1, sha256, sha512.")
            return None
    except Exception as e:
        print(f"An error occurred during hashing: {e}")
        return None


def dictionary_attack(target_hash, hash_type, wordlist_path):
    """
    Attempts to crack a hashed password using a dictionary attack.
    It reads passwords from a wordlist file and hashes each one to compare.
    """
    if not os.path.exists(wordlist_path):
        print(f"Error: Wordlist file not found at '{wordlist_path}'")
        return None

    print(f"\n[+] Starting dictionary attack for hash: {target_hash} ({hash_type})")
    print(f"    Using wordlist: {wordlist_path}")
    start_time = time.time()
    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, word in enumerate(f, 1):
                word = word.strip()  # Remove leading/trailing whitespace including newline
                if not word:  # Skip empty lines
                    continue

                # Hash the word from the wordlist using the specified hash_type
                hashed_word = hash_password(word, hash_type)

                if hashed_word is None:
                    print(f"Skipping word '{word}' due to hashing error.")
                    continue

                # Compare the generated hash with the target hash
                if hashed_word == target_hash:
                    end_time = time.time()
                    print(f"\n[+] Password found! Original password: '{word}'")
                    print(f"    Time taken: {end_time - start_time:.2f} seconds")
                    return word

                # Optional: Print progress for large wordlists
                if line_num % 100000 == 0:
                    print(f"[*] Checked {line_num} words...", end='\r')

        end_time = time.time()
        print(f"\n[-] Password not found in the wordlist after checking {line_num} words.")
        print(f"    Time taken: {end_time - start_time:.2f} seconds")
        return None
    except Exception as e:
        print(f"An error occurred during dictionary attack: {e}")
        return None


def brute_force_attack(target_hash, hash_type, charset, max_length):
    """
    Attempts to crack a hashed password using a brute-force attack.
    It generates all possible combinations of characters up to max_length.
    WARNING: This can be extremely slow for longer passwords or larger charsets.
    """
    print(f"\n[+] Starting brute-force attack for hash: {target_hash} ({hash_type})")
    print(f"    Using charset: '{charset}' up to length {max_length}")
    start_time = time.time()

    for length in range(1, max_length + 1):
        print(f"[*] Trying passwords of length {length}...")
        for attempt in itertools.product(charset, repeat=length):
            password = "".join(attempt)
            hashed_password = hash_password(password, hash_type)

            if hashed_password is None:
                print(f"Skipping password '{password}' due to hashing error.")
                continue

            if hashed_password == target_hash:
                end_time = time.time()
                print(f"\n[+] Password found! Original password: '{password}'")
                print(f"    Time taken: {end_time - start_time:.2f} seconds")
                return password

    end_time = time.time()
    print(f"\n[-] Password not found after brute-forcing up to length {max_length}.")
    print(f"    Time taken: {end_time - start_time:.2f} seconds")
    return None


def main():
    """
    Main function to run the password cracker project.
    Provides options for hashing a password, dictionary attack, or brute-force attack.
    """
    print("---------------------------------------")
    print("      Python Hashed Password Cracker   ")
    print("---------------------------------------")

    while True:
        print("\nChoose an option:")
        print("1. Hash a password")
        print("2. Crack a hash using dictionary attack")
        print("3. Crack a hash using brute-force attack (Warning: Can be very slow!)")
        print("4. Exit")

        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            password = input("Enter the password to hash: ")
            hash_type = input("Enter hash type (md5, sha1, sha256, sha512): ").lower()
            if hash_type not in ['md5', 'sha1', 'sha256', 'sha512']:
                print("Invalid hash type. Please choose from md5, sha1, sha256, sha512.")
                continue
            hashed = hash_password(password, hash_type)
            if hashed:
                print(f"Hashed password ({hash_type}): {hashed}")
        elif choice == '2':
            target_hash = input("Enter the hash to crack: ").strip()
            hash_type = input("Enter the hash type (md5, sha1, sha256, sha512): ").lower()
            if hash_type not in ['md5', 'sha1', 'sha256', 'sha512']:
                print("Invalid hash type. Please choose from md5, sha1, sha256, sha512.")
                continue
            wordlist_path = input("Enter the path to the wordlist file (e.g., 'rockyou.txt'): ").strip()
            dictionary_attack(target_hash, hash_type, wordlist_path)
        elif choice == '3':
            target_hash = input("Enter the hash to crack: ").strip()
            hash_type = input("Enter the hash type (md5, sha1, sha256, sha512): ").lower()
            if hash_type not in ['md5', 'sha1', 'sha256', 'sha512']:
                print("Invalid hash type. Please choose from md5, sha1, sha256, sha512.")
                continue
            charset = input("Enter the character set to use (e.g., 'abcdefghijklmnopqrstuvwxyz0123456789'): ").strip()
            try:
                max_length = int(input("Enter the maximum password length to try (e.g., 5 for short passwords): "))
                if max_length <= 0:
                    print("Maximum length must be a positive integer.")
                    continue
            except ValueError:
                print("Invalid input for maximum length. Please enter an integer.")
                continue
            brute_force_attack(target_hash, hash_type, charset, max_length)
        elif choice == '4':
            print("Exiting the password cracker. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")


if __name__ == "__main__":
    main()
