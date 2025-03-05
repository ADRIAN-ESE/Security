import socket
import logging

# Create a logger
logger = logging.getLogger('caesar_client')
logger.setLevel(logging.DEBUG)

# Create a file handler
file_handler = logging.FileHandler('caesar_client.log')
file_handler.setLevel(logging.DEBUG)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a formatter and attach it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Caesar Cipher shift value
SHIFT = 3

def encrypt(message):
    """Encrypts the message using Caesar Cipher"""
    encrypted_message = ""
    for char in message:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            encrypted_char = chr((ord(char) - ascii_offset + SHIFT) % 26 + ascii_offset)
            encrypted_message += encrypted_char
        else:
            encrypted_message += char
    return encrypted_message

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("localhost", 12345))
    logger.info("Connected to server")

    while True:
        message = input("Client: ")
        encrypted_message = encrypt(message)
        client_socket.sendall(encrypted_message.encode())
        logger.info(f"Client: {message}")
        response = client_socket.recv(1024).decode()
        logger.info(f"Server: {response}")
        print(f"Server: {response}")

    client_socket.close()

if __name__ == "__main__":
    main()