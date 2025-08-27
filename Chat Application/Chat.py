import socket
import threading
import hashlib
import os
from cryptography.fernet import Fernet
import secrets

# Key Generation and Management (Securely store and exchange keys!)
def generate_key():
    return Fernet.generate_key()

def hash_password(password):
    salt = secrets.token_bytes(16)  # Generate a random salt
    salted_password = salt + password.encode('utf-8')
    hashed_password = hashlib.sha256(salted_password).digest()
    return salt, hashed_password

def verify_password(stored_salt, stored_hashed_password, provided_password):
    salted_provided_password = stored_salt + provided_password.encode('utf-8')
    hashed_provided_password = hashlib.sha256(salted_provided_password).digest()
    return hashed_provided_password == stored_hashed_password

# Encryption/Decryption
def encrypt_message(message, key):
    f = Fernet(key)
    encrypted_message = f.encrypt(message.encode('utf-8'))
    return encrypted_message

def decrypt_message(encrypted_message, key):
    f = Fernet(key)
    try:
        decrypted_message = f.decrypt(encrypted_message).decode('utf-8')
        return decrypted_message
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

# Client Handling
def handle_client(client_socket, client_address, key):
    try:
        while True:
            encrypted_message = client_socket.recv(1024)
            if not encrypted_message:
                break

            decrypted_message = decrypt_message(encrypted_message, key)
            if decrypted_message:
                print(f"Received from {client_address}: {decrypted_message}")
                broadcast(encrypted_message, client_socket, key) #broadcast the already encrypted message

    except Exception as e:
        print(f"Client {client_address} disconnected with error: {e}")
    finally:
        clients.remove(client_socket)
        client_socket.close()

# Broadcasting
def broadcast(message, sender_socket, key):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message) #send the encrypted message.
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                clients.remove(client)

# Server Setup
def start_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            clients.append(client_socket)
            print(f"Accepted connection from {client_address}")

            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, server_key))
            client_thread.start()

    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server_socket.close()

# Client Functionality
def start_client(host, port, username, key):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        print("Connected to server.")

        def receive_messages():
            try:
                while True:
                    encrypted_message = client_socket.recv(1024)
                    if not encrypted_message:
                        break
                    decrypted_message = decrypt_message(encrypted_message, key)
                    if decrypted_message:
                        print(f"\nReceived: {decrypted_message}")
            except Exception as e:
                print(f"Receive error: {e}")
            finally:
                client_socket.close()

        receive_thread = threading.Thread(target=receive_messages)
        receive_thread.start()

        while True:
            message = input()
            encrypted_message = encrypt_message(f"{username}: {message}", key)
            client_socket.send(encrypted_message)

    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        client_socket.close()

# Main Execution
if __name__ == "__main__":
    host = '127.0.0.1'  # Localhost
    port = 12345
    clients = []
    server_key = generate_key() #server generates the key

    choice = input("Run as server (s) or client (c)? ").lower()

    if choice == 's':
        start_server(host, port)
    elif choice == 'c':
        username = input("Enter your username: ")
        #In a real application, the key would be securely exchanged.
        print("Important: The key should be securely exchanged before communication. For testing, it is printed below:")
        print(server_key.decode()) #for testing only.
        key_input = input("Enter the server key: ")
        client_key = key_input.encode()
        start_client(host, port, username, client_key)
    else:
        print("Invalid choice.")