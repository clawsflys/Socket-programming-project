📄 README: Seeder for P2P File Sharing
Introduction
This is a Seeder script designed to work with a Tracker in a peer-to-peer (P2P) file-sharing system. The Seeder:

Registers itself with the Tracker, providing its public IP and port.
Listens for leecher connections to provide the requested file in 512 KB chunks.
Sends SHA-256 hash values to ensure data integrity.

Prerequisites
Ensure you have:
✅ Python 3 installed.
✅ The requests module installed (for fetching public IP):
pip install requests
✅ A Tracker already running.

Installation
Clone or Download this repository.
Save the Seeder script as seeder.py.
Ensure you have a file to share (e.g., sample_file.txt).

Usage
Step 1: Start the Tracker
Ensure the Tracker is running before launching the Seeder:
python tracker.py

Step 2: Run the Seeder
Run the Seeder with a file to share:
python seeder.py <file_path> <seeder_name>
Example:
python seeder.py sample_file.txt Seeder1

Optional Arguments:
-p PORT: Specify a custom port (default is 12346).
Example:
python seeder.py sample_file.txt Seeder1 -p 5000

How It Works
    The Seeder registers itself with the Tracker over UDP.
    It listens for leecher connections over TCP.
    When a Leecher connects, the Seeder:
        -Sends the file in 512 KB chunks.
        -Sends a SHA-256 hash for each chunk to verify integrity.
    After the file transfer is complete, the Seeder is ready for new requests.

Expected Output:
When the Seeder runs successfully, you will see:

"Registered with Tracker at 127.0.0.1:5555 with IP: 192.168.1.10:12346
Seeder running on port 12346, serving file: sample_file.txt
Connection from ('192.168.1.15', 56789)
File 'sample_file.txt' served to ('192.168.1.15', 56789)"

Troubleshooting
Issue: "Failed to register with tracker"
    Ensure the Tracker is running before starting the Seeder.
    Check the Tracker IP and port in TRACKER_IP and TRACKER_PORT.

Issue: "Public IP not found. Using localhost."
    Make sure you are connected to the internet.
    Try restarting your network adapter.

Future Improvements
🔹 Implement multi-threaded connections for concurrent file sharing.
🔹 Add progress tracking for leechers.
🔹 Improve error handling for file corruption.

Contributors
Thabang Collen Khumalo
📧 Email: khumalot.collen@gmail.com

