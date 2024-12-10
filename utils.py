import os
import socket
import ssl
import time
from typing import List

# Constants for chunk size and retries
CHUNK_SIZE: int = 500
MAX_RETRIES: int = 3
RETRY_DELAY: int = 1  # in seconds

LIST_BEGIN_MARKER: str = "!!!!!!!!!!!!!!!LIST_BEGIN!!!!!!!!!!!!!!!"
LIST_END_MARKER: str = "!!!!!!!!!!!!!!!!LIST_END!!!!!!!!!!!!!!!!"

# TCP Functions

MIN_CHUNK_SIZE = 1024  # Minimum 1 KB
MAX_CHUNK_SIZE = 65536  # Maximum 64 KB
# Adjust chunk size based on file size
def calculate_chunk_size(file_size):
    if file_size < 1024 * 1024:  # Less than 1 MB
        return MIN_CHUNK_SIZE
    elif file_size < 10 * 1024 * 1024:  # Between 1 MB and 10 MB
        return 8192  # 8 KB
    elif file_size < 100 * 1024 * 1024:  # Between 10 MB and 100 MB
        return 32768  # 32 KB
    else:
        return MAX_CHUNK_SIZE
    
def send_file(sock: socket.socket, filepath: str) -> None:
    '''
    Sends a file over a TCP socket connection with dynamically calculated chunk size.
    Ends with an "END_OF_FILE" signal to indicate transfer completion.

    Args:
        sock (socket.socket): The socket that is being used by the server and client
        filepath (str): The path to the file
    '''
    try:
        file_size = os.path.getsize(filepath)
        chunk_size = calculate_chunk_size(file_size)
        
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                retries = 0
                while retries < MAX_RETRIES:
                    try:
                        sock.sendall(chunk)
                        break
                    except socket.error as e:
                        print(f"Error sending chunk, retrying... ({retries + 1}/{MAX_RETRIES})")
                        retries += 1
                        time.sleep(RETRY_DELAY)
                if retries == MAX_RETRIES:
                    print("Failed to send chunk after retries.")
                    return
        sock.sendall(b"END_OF_FILE")  # Signal end of file transfer
    except Exception as e:
        print(f"Error sending file: {e}")
"""
    Receives a file over a TCP socket connection with dynamically calculated chunk size.
    Stops when an "END_OF_FILE" signal is received.
    """
def recv_file(sock: socket.socket, filename: str) -> None:
    '''
    Receives a file over a TCP socket connection with dynamically calculated chunk size.
    Stops when an "END_OF_FILE" signal is received.

    Args:
        sock (socket.socket): The socket that is being used by the server and client
        filename (str): The path to the file 
    '''
    try:
        with open(filename, 'wb') as f:
            while True:
                retries = 0
                while retries < MAX_RETRIES:
                    try:
                        data = sock.recv(MAX_CHUNK_SIZE)  # Use the maximum chunk size when receiving
                        if b"END_OF_FILE" in data:
                            f.write(data.replace(b"END_OF_FILE", b""))
                            return
                        f.write(data)
                        break
                    except socket.error as e:
                        print(f"Error receiving chunk, retrying... ({retries + 1}/{MAX_RETRIES})")
                        retries += 1
                        time.sleep(RETRY_DELAY)
    except Exception as e:
        print(f"Error receiving file: {e}")

# File Listing

def send_listing(sock: socket.socket, files: List[str]) -> None:
    """
    Sends a directory listing over the socket connection in chunks. Wraps the listing with
    start and end markers for easier parsing on the receiving side.

    Args:
        sock (socket.socket): The socket to send the listing over.
        files (List[str]): A list of file names to include in the directory listing.
    """
    try:
        listing = LIST_BEGIN_MARKER + "\n" + "\n".join(files) + "\n" + LIST_END_MARKER
        total_sent = 0
        while total_sent < len(listing):
            chunk = listing[total_sent:total_sent + CHUNK_SIZE].encode('utf-8')
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    sock.sendall(chunk)
                    total_sent += len(chunk)
                    break
                except socket.error as e:
                    print(f"Error sending listing chunk, retrying... ({retries + 1}/{MAX_RETRIES})")
                    retries += 1
                    time.sleep(RETRY_DELAY)
            if retries == MAX_RETRIES:
                print("Failed to send listing chunk after retries.")
                return
    except Exception as e:
        print(f"Error sending listing: {e}")

def recv_listing(sock: socket.socket) -> None:
    """
    Receives and prints a directory listing over the socket connection. The listing is
    displayed between the specified start and end markers.

    Args:
        sock (socket.socket): The socket to receive the listing from.
    """
    try:
        data = ""
        while True:
            chunk = sock.recv(CHUNK_SIZE).decode('utf-8')
            if LIST_END_MARKER in chunk:
                data += chunk[:chunk.find(LIST_END_MARKER)]
                break
            data += chunk
        
        print(LIST_BEGIN_MARKER)
        listing_content = data.replace(LIST_BEGIN_MARKER, "").strip()
        print(listing_content)
        print(LIST_END_MARKER)
    except Exception as e:
        print(f"Error receiving listing: {e}")

