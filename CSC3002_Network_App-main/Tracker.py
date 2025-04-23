import socket
import threading
import argparse
import requests
import json
import sys
import time

def get_public_ip():
    #get public IP address of the machine
    try:
        response = requests.get("https://api.ipify.org?format=json")
        response.raise_for_status()
        return response.json()["ip"]
    except requests.exceptions.RequestException as e:
        print(f"Error getting public IP: {e}")
        return None

TRACKER_PORT = 5555 # port used by the tracker
RECV_BUFFER_SIZE = 1024 #number of bytes allocated to receive from client
HEARTBEAT_TIMEOUT = 30 #seeder disconnection time out in seconds

class Tracker:
    def __init__(self,host,port):
        #instance variables
        #self.host = host
        self.host = '127.0.0.1'
        self.port = port
        self.seeders = {}   #dictionary to store information of all seeders
        self.last_heartbeat = {} #dictionary to store last heart beat of seeders
    
    def start(self):
        try:
            #create udp socket
            udp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) #(IPv4, UDP)
            #bind socket to initialised host and port numbers
            udp_socket.bind((self.host,self.port))
            #confirm tracker IP and port
            print(f"Tracker listening at {self.host}:{self.port} (host:port)")

            while True:
                #receive RECV_BUFFER_SIZE bytes of data from client
                data, address = udp_socket.recvfrom(RECV_BUFFER_SIZE) #store data and local IP received from client (leecher in this case)
                #create seperate thread to handle multiple clients simultaneously
                threading.Thread(target=self.handle_client, args=(data,address,udp_socket)).start()
        except socket.error as e:
            print(f"Socket error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def handle_client(self, data, address, clientsocket):
        try:
            #decode data received from client
            message = data.decode()
            print(message)
            #split message up into sections seperated by whitespace
            sections = message.split(';')
            print(sections)
            #extract the command from index 0
            command = sections[0]
            print(command)

            #chunk_list = []

            #register seeder in dictionary
            if command == "register":
                #the following info must be determined by the seeder and sent explicitly
                seeder_name = sections[1]
                seeder_ip = sections[2]
                seeder_port = int(sections[3]) #ensure port number is an integer
                #chunk_list = eval(sections[4].decode())
                chunk_list_size = int(sections[4])
                print(chunk_list_size)

                chunk_message = f"get_chunk_list; {self.port+1}"
                clientsocket.sendto(chunk_message.encode(), address)

                chunk_list_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                print(address)
                chunk_list_socket.connect((address[0],self.port+1))
                chunk_list_bytes = bytearray()
                # blocks thread until download is done
                while (sys.getsizeof(chunk_list_bytes) < chunk_list_size):
                    print(len(chunk_list_bytes))
                    chunk_data = (chunk_list_socket.recv(chunk_list_size - len(chunk_list_bytes)))
                    chunk_list_bytes.extend(chunk_data)
                #print(chunk_list_size)
                #chunk_list = eval(chunk_get_response.decode())
                chunk_list_socket.close()
                #print(chunk_list_bytes)
                chunk_list = eval(chunk_list_bytes.decode())
                #chunk_list = chunk_list_bytes.decode()
                print(chunk_list)

                self.seeders[seeder_name] = {"ip": seeder_ip, "port": seeder_port, "chunk_list_size": chunk_list_size, "chunk_list": chunk_list} #store ip and port in dictionary with seeder_name as key.
                print(f"Seeder {seeder_name} successfully registered from IP: {address} (Local Router IP)") # display local ip of the router of successfully registered machine

            #return list of seeders
            elif command == "list_seeder":
                chunk_list_port = address[1]+1
                available_seeders = [((seeder_name, seeder_info["ip"], seeder_info["port"], chunk_list_port, seeder_info["chunk_list_size"])) for seeder_name, seeder_info in self.seeders.items()] #list of tuples (seeders name, public ip, port number)
                #clientsocket.sendto(f"{chunk_list_port}".encode())
                print(available_seeders)
                clientsocket.sendto(str(available_seeders).encode(), address) #send list of seeders to leecher

            elif command == "get_chunk_list":
                seeder_name = sections[1]
                chunk_list_port = address[1]+1
                chunk_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print(address)
                chunk_socket.bind((address[0], chunk_list_port))
                chunk_socket.listen(1)
                conn, addr = chunk_socket.accept()
                message = str(self.seeders[seeder_name]["chunk_list"])
                conn.sendall(message.encode())  # Send to tracker
                print("sent chunk list")
                chunk_socket.close()

            elif command =="heartbeat":
                seeder_name = sections[1]
                if seeder_name in self.seeders: #check if seeder name is in seeder list
                    self.last_heartbeat[seeder_name] = time.time() #add the heart beat time stamp to the heartbeat dictionary
                    print(f"Heartbeat from {seeder_name}") 

            else:
                print(f"Unknown command from {address}: {command}")

        except (ValueError, IndexError) as e:
            print(f"Invalid data format from {address}: {e}")
        except socket.error as e:
            print(f"Socket error with {address}: {e}")
        except KeyError as e:
            print(f"Key error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    
    #check if any seeders have disconnected
    def check_for_disconnections(self):  
        while True:
            current_time = time.time() #system current time of checking
            disconnected_seeders = [] # store disconnected seeder names/keys

            #add timed out seeders to disconnected list
            for seeder_name , last_time in self.last_heartbeat.items(): 
                if current_time - last_time > HEARTBEAT_TIMEOUT: # check if seeder has timed out
                    disconnected_seeders.append(seeder_name) #add seeder to disconnected seeders list

            #remove disconnected seeders from the seeders list
            for seeder_name in disconnected_seeders:
                if seeder_name in self.seeders: 
                    del self.seeders[seeder_name]
                    del self.last_heartbeat[seeder_name]
                    print(f"Seeder {seeder_name} disconnected.")
            time.sleep(10) #check every 10 seconds.

if __name__ == "__main__":
    #create command line interface for using different ports
    parser = argparse.ArgumentParser(description="Run tracker.")
    parser.add_argument("-p", "--port", type=int, default=TRACKER_PORT, help="Port number to use")
    args = parser.parse_args()

    #determine host IP (public or local)
    public_ip = get_public_ip()
    if public_ip:
        host = public_ip
        print(f"Using public IP: {host}")
    else:
        host = "127.0.0.1"
        print("Public IP not found. Using localhost.")

    #create tracker and start it
    tracker = Tracker(host, args.port)
    tracker.start()