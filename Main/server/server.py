# 2024 © Idan Hazay
# Import libraries

from modules import client_requests, networking, protocol

from modules.config import *
from modules.errors import Errors
from modules.logger import Logger

import socket, traceback, time, threading, sys
from requests import get


class Application:
    def __init__(self, addr):
        self.clients = {}
        self.bytes_recieved = {}
        self.bytes_sent = {}

        self.files_uploading = {}
        self.all_to_die = False
        self.network = networking.Network(self.clients, self.bytes_recieved, self.bytes_sent)
        self.cr = client_requests.ClientRequests()
        self.protocol = protocol.Protocol(self.network, self.clients, self.cr, self.files_uploading)
        self.addr = addr
        
        self.start()
    
    def start(self):
        threads = []
        self.srv_sock = socket.socket()
        self.srv_sock.bind(self.addr)
        self.srv_sock.listen(20)

        print(f"Server listening on {self.addr}")
        
        try:
            self.public_ip = get('https://api.ipify.org').content.decode('utf8')
        except Exception:
            self.public_ip = "No IP found"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))  # Connect to a public DNS server (Google's in this case)
                self.local_ip = s.getsockname()[0]
        except:
            self.local_ip = "127.0.0.1"
        
        print(f"Public server ip: {self.public_ip}, local server ip: {self.local_ip}")

        self.srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        i = 1
        try:
            self.network.encryption.create_keys()
            self.network.encryption.load_keys()
            scheduler = threading.Thread(target=self.cleaner)
            scheduler.start()
        except:
            print(traceback.format_exc())
            self.srv_sock.close()
            return

        dhcp_listener = threading.Thread(target=self.network.dhcp_listen, args=(self.local_ip, self.addr[1]))
        dhcp_listener.start()
        
        print('Main thread: before accepting ...\n')
        while True:
            cli_sock, addr = self.srv_sock.accept()
            t = threading.Thread(target=self.handle_client, args=(cli_sock, str(i), addr))   # Accepting client and assigning id
            t.start()
            i += 1
            threads.append(t)
            if i > 100000000:
                print('\nMain thread: going down for maintenance')
                break

        self.all_to_die = True
        print('Main thread: waiting to all clints to die')
        for t in threads:
            t.join()

        self.srv_sock.close()
        print('Bye ..')
    
# Main function and client handling, start of code

    def handle_client(self, sock, tid, addr):
        """
        Client handling function
        Sends RSA public key and recieves shared secret for secure connection
        """
        try:
            finish = False
            print(f'New Client number {tid} from {addr}')
            self.bytes_sent[tid] = 0
            self.bytes_recieved[tid] = 0
            start = self.network.recv_data(sock, tid)
            code = start.split(b"|")[0]
            self.clients[tid] = Client(tid, "guest", "guest", 0, 0, None, False)   # Setting client state
            if (code == b"RSAR"):
                shared_secret = self.network.encryption.rsa_exchange(sock, tid)
            if (shared_secret == ""):
                return

            self.clients[tid].shared_secret = shared_secret
            self.clients[tid].encryption = True
            
        except Exception:
            print(traceback.format_exc())
            # Releasing clienk and closing socket
            print(f'Client {tid} connection error')
            if (tid in self.clients):
                self.clients[tid] = None
            sock.close()
            return
        while not finish and self.clients[tid] != None:   # Main client loop
            if self.all_to_die:
                print('will close due to main server issue')
                break
            try:
                # Recieving data and  handling client
                entire_data = self.network.recv_data(sock, tid)
                t = threading.Thread(target=self.handle_request, args=(entire_data, tid, sock))
                t.start()
                
            except socket.error as err:
                print(f'Socket Error exit client loop: err:  {err}')
                break
            except Exception as err:
                print(f'General Error %s exit client loop: {err}')
                print(traceback.format_exc())
                break
        print(f'Client {tid} Exit')   # Releasing clienk and closing socket
        self.clients[tid] = None
        sock.close()
    
    def handle_request(self, request, tid, sock):
        """
        Getting client request and parsing it
        If some error occured or no response return general error
        """
        global finish
        try:
            to_send = self.protocol.protocol_build_reply(request, tid, sock)
            if to_send == None:
                self.clients[tid] = None
                print(f"Client {tid} disconnected")
                return
            to_send = to_send.encode()
            self.network.send_data(sock, tid, to_send)
            if (to_send == b"EXTR"):
                self.clients[tid] = None
                print(f"Client {tid} disconnected")

        except Exception as err:
            print(traceback.format_exc())
            to_send = Errors.GENERAL.value
            self.network.send_data(sock, tid, to_send.encode())

    def cleaner(self):
        while True:
            self.cr.clean_db(self.files_uploading)
            time.sleep(100)
    


class Client:
    """
    Client class for handling a client
    """

    def __init__(self, id, user, email, subscription_level, admin_level, shared_secret, encryption):
        self.id = id
        self.user = user
        self.email = email
        self.subscription_level = subscription_level
        self.admin_level = admin_level
        self.shared_secret = shared_secret
        self.encryption = encryption
        self.cwd = f"{cloud_path}\\{self.user}"

def main(addr):
    app = Application(addr)


if __name__ == '__main__':   # Run main
    sys.stdout = Logger()
    port = 3102
    if len(sys.argv) == 2:
        port = sys.argv[1]
    main(("0.0.0.0", int(port)))
