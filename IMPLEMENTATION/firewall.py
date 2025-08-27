import socket
import sys
import threading

# Define the rules for the firewall
allowed_ips = ["127.0.0.1"]  # Add allowed IPs here
blocked_ips = ["192.168.1.100"]  # Add blocked IPs here
allowed_ports = [80, 443]  # List of allowed ports


# Firewall function to check if the connection is allowed
def is_allowed(ip, port):
    if ip in blocked_ips:
        print(f"Connection from {ip} is blocked.")
        return False
    if port not in allowed_ports:
        print(f"Connection to port {port} is blocked.")
        return False
    if ip in allowed_ips:
        print(f"Connection from {ip} is allowed.")
        return True
    return False


# Handle incoming client connections
def handle_client(client_socket, client_address):
    ip, port = client_address
    print(f"Connection attempt from {ip}:{port}")

    if is_allowed(ip, port):
        client_socket.send(b"Welcome, connection accepted!\n")
        print(f"Accepted connection from {ip}:{port}")
    else:
        client_socket.send(b"Access Denied.\n")
        print(f"Rejected connection from {ip}:{port}")

    client_socket.close()


# Main firewall server function
def start_firewall(host, port):
    firewall_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    firewall_socket.bind((host, port))
    firewall_socket.listen(5)

    print(f"Firewall is running on {host}:{port}...")

    while True:
        # Accept incoming client connections
        client_socket, client_address = firewall_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()


# Main function to run the firewall
if __name__ == "__main__":
    # Set the host and port to listen on
    host = '0.0.0.0'  # Listen on all interfaces
    port = 8080  # Choose the port

    # Start the firewall
    try:
        start_firewall(host, port)
    except KeyboardInterrupt:
        print("Firewall stopped.")
        sys.exit(0)
