import socket
import json
import threading
import os
import hashlib
import sys

CHUNK_SIZE = 512 * 1024  # 512 KB chunk size
TRACKER_IP = "127.0.0.1"  # Change this to the tracker's actual IP
TRACKER_PORT = 5555  # Must match the tracker's listening port

def assemble_file(chunk_map, output_file):
    with open(output_file, 'wb') as file:
        for index in sorted(chunk_map.keys()):  # Writes chunks in order based on their index
            file.write(chunk_map[index])
    print("File assembly complete!")

def receive_chunk(peer, chunk_index, chunk_map, chunk_list, output_file):
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #client.connect((peer[1], PORT))  # Connects to the peer to request a chunk
        #client.connect((peer[1].strip(), peer[2]))
        client.connect(('localhost', peer[2]))
        #print(peer[1])
        client.send(str(chunk_index).encode())  # Requests the specific chunk by index
        chunk = client.recv(CHUNK_SIZE)  # Receives the chunk data
        #chunk_hash = client.recv(64).decode()  # Receives the hash of the chunk for verification
        chunk_hash = chunk_list[chunk_index]
        if hashlib.sha256(chunk).hexdigest() == chunk_hash:  # Validates integrity
            chunk_map[chunk_index] = chunk  # Stores the valid chunk in the chunk map
            #print(f"Chunk {chunk_index} downloaded from {peer}")
        client.close()
    except:
        print(f"Failed to get chunk {chunk_index} from {peer}")

tracker = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tracker.connect((TRACKER_IP, TRACKER_PORT))
print("Connected to tracker")

tracker.send(b'list_seeder')  # Requests peer list
#peers = json.loads(tracker.recv(1024).decode())  # Receives peer data
peers = eval(tracker.recv(1024))
print(peers)
#peer.send(b'get_chunk_list')


if not peers:
    print("No peers found!")
    sys.exit()

chunk_map = {}  # Dictionary to store downloaded chunks
threads = []  # List to store threads for parallel downloading

output_file = "C:/Users/luke/Downloads/CSC3002_Network_App-main(1)/CSC3002_Network_App-main/rick_download.mkv"

for peer in peers:
    tracker.send(b'get_chunk_list;' + peer[0].encode())
    
    chunk_list_size = peer[4]
    chunk_list_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    chunk_list_socket.connect((TRACKER_IP, peer[3]))

    chunk_list_bytes = bytearray()
    # blocks thread until download is done
    while (sys.getsizeof(chunk_list_bytes) < chunk_list_size):
        #print(len(chunk_list_bytes))
        chunk_data = (chunk_list_socket.recv(chunk_list_size - len(chunk_list_bytes)))
        chunk_list_bytes.extend(chunk_data)
    chunk_list_socket.close()
    chunk_list = eval(chunk_list_bytes.decode())

    print(chunk_list[0])
    print(peer[0:3])
    print(peer)
    #receive_chunk(peer[0:3], 0, chunk_map, chunk_list, output_file)
    #receive_chunk(peer[0:3], 1, chunk_map, chunk_list, output_file)
    #receive_chunk(peer[0:3], 2, chunk_map, chunk_list, output_file)

    
    for chunk_index in chunk_list.keys():
        thread = threading.Thread(target=receive_chunk, args=(peer[0:3], chunk_index, chunk_map, chunk_list, output_file))  # Creates a download thread
        threads.append(thread)
        thread.start()


tracker.close()

thread_count = 0;
print("          [---------]")
print("Progress: [", end='')
for thread in threads:
    thread.join()  # Waits for all threads to finish downloading
    thread_count += 1
    if thread_count >= len(threads) / 10:
        print("#", end='')
        thread_count = 0;
print("]")
print("          [---------]")
        
assemble_file(chunk_map, output_file)  # Reassembles the file after downloading
