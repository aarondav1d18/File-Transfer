import socket
import os
import sys
import ssl
from utils import (
    recv_file,
    send_file,
    send_listing,
     )

UPLOAD_DIRECTORY = "uploaded_files"

def start_server(port: int) -> None:
    """
    Starts the server on the specified port, using either TCP or TLS based on the protocol setting.
    Creates an upload directory if it does not exist.
    
    Args:
        port (int): The port number on which to start the server.
    """
    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)
    
    try:
        srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv_sock.bind(("", port))
        srv_sock.listen(5)
        print(f"Server up and running on port {port}...")

        while True:
            cli_sock, cli_addr = srv_sock.accept()
            print(f"Connection established with {cli_addr}")
            handle_client(cli_sock)

    except socket.error as e:
        print(f"Failed to start server: {e}")
    except KeyboardInterrupt:
        print("\nServer shutting down...")

def handle_client(cli_sock: socket.socket) -> None:
    """
    Handles requests from a connected client, supporting 'put', 'get', and 'list' commands.
    
    Args:
        cli_sock (socket.socket): The client socket connected to the server.
    """
    try:
        request: str = cli_sock.recv(1024).decode('utf-8').strip()
        if not request:
            print("Empty request from client. Disconnecting...")
            return
        
        parts: list[str] = request.split(maxsplit=1)
        command: str = parts[0]
        filename: str = parts[1].strip() if len(parts) > 1 else None

        if command == "put" and filename:
            file_path: str = os.path.join(UPLOAD_DIRECTORY, filename)
            if os.path.exists(file_path):
                cli_sock.sendall("Error: File already exists".encode('utf-8'))
            else:
                cli_sock.sendall("OK".encode('utf-8'))
                recv_file(cli_sock, file_path)
                cli_sock.sendall("File saved successfully on the server.".encode('utf-8'))
        elif command == "get" and filename:
            file_path: str = os.path.join(UPLOAD_DIRECTORY, filename)
            if os.path.exists(file_path):
                cli_sock.sendall("OK".encode('utf-8'))
                send_file(cli_sock, file_path)
            else:
                cli_sock.sendall("Error: File not found".encode('utf-8'))
        elif command == "list":
            files: list[str] = os.listdir(UPLOAD_DIRECTORY)
            send_listing(cli_sock, files)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        cli_sock.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        sys.exit(1)
    port: int = int(sys.argv[1])
    start_server(port)
