import hashlib
import itertools
import string
import time

def brute_force_crack(password, charset, max_length):
    """
    Brute Force Cracking
    """
    start_time = time.time()
    for length in range(1, max_length + 1):
        for attempt in itertools.product(charset, repeat=length):
            attempt = ''.join(attempt)
            if hashlib.sha256(attempt.encode()).hexdigest() == password:
                end_time = time.time()
                print(f"Password cracked: {attempt} in {end_time - start_time:.2f} seconds")
                return

def dictionary_crack(password, wordlist):
    """
    Dictionary Cracking
    """
    start_time = time.time()
    with open(wordlist, 'r') as f:
        for word in f.readlines():
            word = word.strip()
            if hashlib.sha256(word.encode()).hexdigest() == password:
                end_time = time.time()
                print(f"Password cracked: {word} in {end_time - start_time:.2f} seconds")
                return

def rainbow_table_crack(password, rainbow_table):
    """
    Rainbow Table Cracking
    """
    start_time = time.time()
    with open(rainbow_table, 'r') as f:
        for line in f.readlines():
            hash, plaintext = line.split(':')
            if hash == password:
                end_time = time.time()
                print(f"Password cracked: {plaintext} in {end_time - start_time:.2f} seconds")
                return

if __name__ == "__main__":
    password = input("Enter a password to crack: ")
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    print("Brute Force Cracking")
    brute_force_crack(password_hash, string.ascii_letters + string.digits, 10)

    print("\nDictionary Cracking")
    dictionary_crack(password_hash, 'wordlist.txt')

    print("\nRainbow Table Cracking")
    rainbow_table_crack(password_hash, 'rainbow_table.txt')