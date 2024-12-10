import socket
import sys
import os
import shlex
import argparse
from utils import (
    recv_file, 
    send_file, 
    recv_listing, 
    )
"""
    Entry point for the client application. Parses command-line arguments to determine the host, port,
    command (put, get, list), and filepath (if applicable). Depending on the protocol (TCP, UDP, TLS),
    establishes a connection to the server, sends requests, and handles responses accordingly.
    """
def main(args) -> None:
    '''
    Entry point for the client application. Parses command-line arguments to determine the host, port,
    command (put, get, list), and filepath (if applicable).Then establishes a connection to the server, 
    sends requests, and handles responses accordingly.

    Args:
        args (Namespace): A namespace of the passed arguments from the user
    '''
    
    host: str = args.host
    port: int = int(args.port)
    command: str = args.command
    print(args)
    filepath: str = args.filepath

    try:
        cli_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cli_sock.connect((host, port))
        print(f"Connected to {host}:{port}")

        if command == "put" and filepath:
            if not os.path.exists(filepath):
                print(f"Error: File '{filepath}' does not exist.")
                cli_sock.close()
                return
            filename: str = os.path.basename(filepath)
            cli_sock.sendall(f"put {filename}".encode('utf-8'))
            response: str = cli_sock.recv(1024).decode('utf-8')
            if response.startswith("Error"):
                print(f"Server: {response}")
            else:
                send_file(cli_sock, filepath)
                print(f"File '{filename}' uploaded successfully.")
        elif command == "get" and filepath:
            filename: str = os.path.basename(filepath)
            cli_sock.sendall(f"get {filename}".encode('utf-8'))
            response: str = cli_sock.recv(1024).decode('utf-8')
            if response.startswith("Error"):
                print(f"Server: {response}")
            else:
                recv_file(cli_sock, filename)
                print(f"File '{filename}' downloaded successfully.")
        elif command == "list":
            cli_sock.sendall("list".encode('utf-8'))
            recv_listing(cli_sock)

        cli_sock.close()

    except socket.error as e:
        print(f"Socket error: {e}")
    except KeyboardInterrupt:
        print("\nConnection interrupted. Exiting...")
    finally:
        cli_sock.close()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Client application for file operations")
    parser.add_argument("host", type=str, help="The hostname or IP address of the server")
    parser.add_argument("port", type=int, help="The port number of the server")
    parser.add_argument("command", type=str, choices=["put", "get", "list"], help="Command to execute")
    parser.add_argument("filepath", nargs="?", type=str, help="Path to the file (if applicable)")
    
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_arguments()
    main(args)
