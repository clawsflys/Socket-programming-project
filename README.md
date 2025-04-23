# README: Tracker.py

#Overview
This python script, Tracker.py, implements a tracker for a peer to peer (P2P) file-sharing system. The primary role if this tracker is to maintain a list of available seeders and their information, that leechers can use to discover and connect to for file downloads.

## Functionality

1.  **Seeder Registration:**
    * Seeders can register with the tracker by sending a "register" command, including their name, public IP, port, and the size of the chunk list.
    * Upon receiving a registration request, the tracker initiates a TCP connection with the seeder on a port incremented by one from the trackers port, to receive the seeders chunk list.
    * The tracker stores this information in a dictionary, associating each seeder's name with their IP, port, chunk list size, and chunk list.

2.  **Leecher Seeder List Retrieval:**
    * Leechers can request a list of available seeders by sending a "list\_seeder" command.
    * The tracker responds with a list of tuples, where each tuple contains the seeder's name, public IP, port, the port of the chunk list TCP connection, and the size of the chunk list.

3.  **Chunk List Retrieval:**
    * When a leecher recieves the list of seeders, it also recieves the port number of the TCP connection that the seeders chunk list can be retrieved from.

## Usage

1.  **Running the Tracker:**
    * Open a terminal or command prompt.
    * Navigate to the directory containing `tracker.py`.
    * Run the script using Python: `python tracker.py`.
    * You can specify a custom port using the `-p` or `--port` argument: `python tracker.py -p <port_number>`. If no port is specified, the default port (5555) will be used.

2.  **Port Forwarding:**
    * If running the tracker on a machine behind a NAT router, ensure that the specified port (and the port incremented by one) is forwarded to the machine running the tracker.

3.  **Seeder Registration Format:**
    * Seeders must send a UDP message with the format: `register; <seeder_name>; <seeder_ip>; <seeder_port>; <chunk_list_size>`.
    * Replace `<seeder_name>`, `<seeder_ip>`, and `<seeder_port>` with the appropriate values.
    * `<chunk_list_size>` is an integer representing the size of the chunk list in bytes.

4.  **Leecher Seeder List Request:**
    * Leechers must send a UDP message with the command: `list_seeder`.

## Implementation Details

* The tracker uses UDP for communication with seeders and leechers.
* The tracker uses TCP to recieve the chunk list from the seeders.
* The `argparse` module is used to handle command-line arguments for specifying the port.
* The `requests` module is used to obtain the machine's public IP address.
* The tracker uses threads to handle multiple client requests concurrently.
* The chunk list is sent as a string representation of a Python list.

## Notes

* Ensure that the seeder's public IP and port are correctly provided during registration.
* The tracker currently runs on the loopback address if it fails to get a public IP.
* The tracker does not implement seeder disconnection handling.
* The port number for the chunk list is the trackers port number incremented by one.
* The chunk list is sent as a string of a python list, and must be evaluated.
