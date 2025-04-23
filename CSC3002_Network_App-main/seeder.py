import socket
import os
import sys
import hashlib
import argparse
import requests  # Import requests to fetch public IP
import json
import threading
import time

CHUNK_SIZE = 512 * 1024  # 512 KB chunk size
TRACKER_IP = "127.0.0.1"  # Change this to the tracker's actual IP
TRACKER_PORT = 5555  # Must match the tracker's listening port
HEARTBEAT_INTERVAL = 10 #notify tracker seeder is still connected 

def get_file_chunks(file_path):
    """Generator function to read a file in chunks."""
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(CHUNK_SIZE)  # Read 512 KB at a time
                if not chunk:
                    break
                yield chunk
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        return []  # Return empty list to prevent further errors:

def split_file(file_path):
    chunks = []
    for chunk in get_file_chunks(file_path):  # Read file in chunks
            chunk_hash = hashlib.sha256(chunk).hexdigest()  # Computes the SHA-256 hash of the chunk
            chunks.append((chunk, chunk_hash))  # Stores the chunk and its hash for integrity verification
    return chunks

def calculate_hash(chunk):
    """Calculates SHA-256 hash for a given chunk."""
    sha256 = hashlib.sha256()
    sha256.update(chunk)
    return sha256.hexdigest()

def get_public_ip():
    """Fetches the external (public) IP of the seeder."""
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        response.raise_for_status()
        return response.json()["ip"]
    except requests.exceptions.RequestException:
        return None  # If fetching fails, return None

def register_with_tracker(seeder_name, port, chunks):
    """Registers this seeder with the tracker using UDP."""
    try:
        public_ip = get_public_ip()
        if not public_ip:
            print("Warning: Could not determine public IP. Defaulting to localhost.")
            public_ip = "127.0.0.1"  # Use localhost if public IP is unavailable

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create UDP socket
        
        # Generates chunk hashes
        chunk_list = {i: hashlib.sha256(chunk[0]).hexdigest() for i, chunk in enumerate(chunks)}
        
        #print(chunk_list)
        #print(f"{chunk_list}".encode())
        #json_chunk_list = json.dumps(chunk_list)
        #binary_chunk_list = json_chunk_list.encode()
        message2 = f"{chunk_list}"
        chunk_list_size = sys.getsizeof(message2)
        message1 = f"register; {seeder_name}; {public_ip}; {port}; {chunk_list_size}"  # Format registration message
        #print()
        #print(message)
        udp_socket.sendto(message1.encode(), (TRACKER_IP, TRACKER_PORT))  # Send to tracker
        print("sent metadata message")
        response = (udp_socket.recv(1024)).decode()
        sections = response.split(';')
        command = sections[0]
        print(sections)
        print(message2)
        if command == 'get_chunk_list':
            port = int(sections[1])
            chunk_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            chunk_socket.bind((TRACKER_IP, port))
            chunk_socket.listen(1)
            conn, addr = chunk_socket.accept()
            conn.sendall(message2.encode())  # Send to tracker
            print("sent chunk list")
            print(chunk_list_size)
            chunk_socket.close()
        print(f"Registered with Tracker at {TRACKER_IP}:{TRACKER_PORT} with IP: {public_ip}:{port}")
    except socket.error as e:
        print(f"Failed to register with tracker (socket error): {e}")
    except Exception as e:
        print(f"Failed to register with tracker (general error): {e}")

#let tracker know you are still seeding
def send_heartbeat(seeder_name, port):
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #create socket
        message = f"heartbeat;{seeder_name};{port}"  
        udp_socket.sendto(message.encode(), (TRACKER_IP, TRACKER_PORT))
        udp_socket.close()
    except socket.error as e:
        print(f"Heartbeat failed: {e}")   

#create a thread that sends the seeders heartbeat on a loop         
def start_heartbeat_thread(seeder_name, port):
    #function to be passed to thread
    def heartbeat_loop():
        while True:
            send_heartbeat(seeder_name, port)
            time.sleep(HEARTBEAT_INTERVAL)

    heartbeat_thread = threading.Thread(target=heartbeat_loop) #create thread
    heartbeat_thread.daemon = True  #allow program to exit if thread is still running
    heartbeat_thread.start() 
    
def start_seeder(file_path, seeder_name, port=12346):
    try:
        """Starts the Seeder server to provide file chunks to leechers."""
        chunks = split_file(file_path)
        #print(chunks[0])
        register_with_tracker(seeder_name, port, chunks)  # Register Seeder with Tracker

        start_heartbeat_thread(seeder_name, port) #start heartbeat thread

        seeder_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create TCP socket
        seeder_socket.bind(("0.0.0.0", port))  # Bind to all network interfaces
        seeder_socket.listen(1024)  # Allow up to 1024 concurrent connections
        print(f"Seeder running on port {port}, serving file: {file_path}")

        while True:
            conn, addr = seeder_socket.accept()  # Accept incoming connection from a leecher
            print(f"Connection from {addr}")
            """
            with conn:
                for chunk in get_file_chunks(file_path):  # Read file in chunks
                    chunk_hash = calculate_hash(chunk)  # Compute hash for integrity check
                    conn.sendall(chunk)  # Send chunk data
                    conn.sendall(chunk_hash.encode())  # Send hash to verify chunk integrity
            print(f"File '{file_path}' served to {addr}")
            """
            try:
                chunk_index = int((conn.recv(64)).decode())
                conn.sendall(chunks[chunk_index][0])
                print(f"File '{file_path}' chunk {chunk_index} served to {addr}")

            except (ValueError, IndexError) as e:
                print(f"Error serving chunk to {addr}: {e}")
            except socket.error as e:
                print(f"Socket error with {addr}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while serving {addr}: {e}")

    except socket.error as e:
        print(f"Seeder socket error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in the seeder: {e}")

# Run the Seeder with command-line options
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Seeder.")
    parser.add_argument("file", help="Path to the file to seed")
    parser.add_argument("name", help="Seeder name (must be unique)")
    parser.add_argument("-p", "--port", type=int, default=12346, help="Port number to use")
    args = parser.parse_args()

    start_seeder(args.file, args.name, port=args.port)
