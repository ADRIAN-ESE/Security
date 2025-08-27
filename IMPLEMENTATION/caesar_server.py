import socket
import threading
import logging

# Create a logger
logger = logging.getLogger('caesar_server')
logger.setLevel(logging.DEBUG)

# Create a file handler
file_handler = logging.FileHandler('caesar_server.log')
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

def decrypt(message):
    """Decrypts the message using Caesar Cipher"""
    decrypted_message = ""
    for char in message:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            decrypted_char = chr((ord(char) - ascii_offset - SHIFT) % 26 + ascii_offset)
            decrypted_message += decrypted_char
        else:
            decrypted_message += char
    return decrypted_message

def handle_client(client_socket, address):
    logger.info(f"Connected to {address}")

    while True:
        message = client_socket.recv(1024).decode()
        if not message:
            break
        decrypted_message = decrypt(message)
        logger.info(f"Client: {decrypted_message}")
        response = input("Server: ")
        encrypted_response = ""
        for char in response:
            if char.isalpha():
                ascii_offset = 65 if char.isupper() else 97
                encrypted_char = chr((ord(char) - ascii_offset + SHIFT) % 26 + ascii_offset)
                encrypted_response += encrypted_char
            else:
                encrypted_response += char
        client_socket.sendall(encrypted_response.encode())
        logger.info(f"Server: {response}")

    logger.info(f"Disconnected from {address}")
    client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 12345))
    server_socket.listen(5)
    logger.info("Server listening on port 12345...")

    while True:
        client_socket, address = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
        client_thread.start()

if __name__ == "__main__":
    main()