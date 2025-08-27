class VigenereCipher:
    def __init__(self, key):
        self.key = key

    def encrypt(self, plaintext):
        """Encrypt plaintext using Vigenère Cipher"""
        ciphertext = ""
        key_index = 0
        for char in plaintext:
            if char.isalpha():
                shift = ord(self.key[key_index % len(self.key)].lower()) - 97
                if char.isupper():
                    ciphertext += chr((ord(char) - 65 + shift) % 26 + 65)
                else:
                    ciphertext += chr((ord(char) - 97 + shift) % 26 + 97)
                key_index += 1
            else:
                ciphertext += char
        return ciphertext

    def decrypt(self, ciphertext):
        """Decrypt ciphertext using Vigenère Cipher"""
        plaintext = ""
        key_index = 0
        for char in ciphertext:
            if char.isalpha():
                shift = ord(self.key[key_index % len(self.key)].lower()) - 97
                if char.isupper():
                    plaintext += chr((ord(char) - 65 - shift) % 26 + 65)
                else:
                    plaintext += chr((ord(char) - 97 - shift) % 26 + 97)
                key_index += 1
            else:
                plaintext += char
        return plaintext


class ChatSystem:
    def __init__(self, key):
        self.cipher = VigenereCipher(key)

    def send_message(self, message):
        """Encrypt and send message"""
        encrypted_message = self.cipher.encrypt(message)
        return encrypted_message

    def receive_message(self, encrypted_message):
        """Receive and decrypt message"""
        decrypted_message = self.cipher.decrypt(encrypted_message)
        return decrypted_message


# Example usage
key = "secretkey"

# Create chat system instances for Alice and Bob
alice = ChatSystem(key)
bob = ChatSystem(key)

# Alice sends a message to Bob
message = "Hello, Bob!"
encrypted_message = alice.send_message(message)
print(f"Alice sends: {encrypted_message}")

# Bob receives and decrypts the message
decrypted_message = bob.receive_message(encrypted_message)
print(f"Bob receives: {decrypted_message}")

# Bob sends a message to Alice
message = "Hi, Alice!"
encrypted_message = bob.send_message(message)
print(f"Bob sends: {encrypted_message}")

# Alice receives and decrypts the message
decrypted_message = alice.receive_message(encrypted_message)
print(f"Alice receives: {decrypted_message}")