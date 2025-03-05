# Caesar Cipher
def caesar_encrypt(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
        else:
            result += char
    return result


def caesar_decrypt(text, shift):
    return caesar_encrypt(text, -shift)


# Vigenère Cipher
def vigenere_encrypt(text, key):
    result = ""
    key_index = 0
    for char in text:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            key_char = key[key_index % len(key)].lower()
            shift = ord(key_char) - 97
            result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
            key_index += 1
        else:
            result += char
    return result


def vigenere_decrypt(text, key):
    result = ""
    key_index = 0
    for char in text:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            key_char = key[key_index % len(key)].lower()
            shift = ord(key_char) - 97
            result += chr((ord(char) - ascii_offset - shift) % 26 + ascii_offset)
            key_index += 1
        else:
            result += char
    return result


# XOR Cipher
def xor_encrypt(text, key):
    result = ""
    for char in text:
        result += chr(ord(char) ^ ord(key))
    return result


def xor_decrypt(text, key):
    return xor_encrypt(text, key)


# Main Program
def main():
    while True:
        print("Encryption and Decryption Tool")
        print("-------------------------------")
        print("1. Caesar Cipher")
        print("2. Vigenère Cipher")
        print("3. XOR Cipher")
        print("4. Quit")
        choice = input("Choose an option: ")

        if choice == "1":
            text = input("Enter text: ")
            shift = int(input("Enter shift value: "))
            encrypted = caesar_encrypt(text, shift)
            print("Encrypted:", encrypted)
            decrypted = caesar_decrypt(encrypted, shift)
            print("Decrypted:", decrypted)
        elif choice == "2":
            text = input("Enter text: ")
            key = input("Enter key: ")
            encrypted = vigenere_encrypt(text, key)
            print("Encrypted:", encrypted)
            decrypted = vigenere_decrypt(encrypted, key)
            print("Decrypted:", decrypted)
        elif choice == "3":
            text = input("Enter text: ")
            key = input("Enter key (single character): ")
            encrypted = xor_encrypt(text, key)
            print("Encrypted:", encrypted)
            decrypted = xor_decrypt(encrypted, key)
            print("Decrypted:", decrypted)
        elif choice == "4":
            break
        else:
            print("Invalid option. Please choose again.")


if __name__ == "__main__":
    main()