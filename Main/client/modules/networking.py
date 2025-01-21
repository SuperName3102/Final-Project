# 2024 © Idan Hazay

import modules.encrypting as encrypting
from modules.config import *
import struct, socket, psutil, time


class Network():
    def __init__(self, log = False):
        self.log = log
        
    def set_sock(self, socket):
        self.sock = socket

    def set_secret(self, secret):
        self.shared_secret = secret

    def logtcp(self, dir, byte_data):
        """
        Loggs the recieved data to console
        """
        if self.log:
            try:
                if (str(byte_data[0]) == "0"):print("")
            except AttributeError:
                return
            if dir == 'sent':   # Sen/recieved labels
                print(f'C LOG:Sent     >>>{byte_data}')
            else:
                print(f'C LOG:Recieved <<<{byte_data}')


    def send_data_wrap(self, bdata, encryption):
        """
        Send data to server
        Adds data encryption
        Adds length
        Loggs the encrypted and decrtpted data for readablity
        Checks if encryption is used
        """
        if (encryption):
            encrypted_data = encrypting.encrypt(bdata, self.shared_secret)
            data_len = struct.pack('!l', len(encrypted_data))
            to_send = data_len + encrypted_data
            to_send_decrypted = str(len(bdata)).encode() + bdata
            self.logtcp('sent', to_send)
            self.logtcp('sent', to_send_decrypted)
        else:
            data_len = struct.pack('!l', len(bdata))
            to_send = data_len + bdata
            self.logtcp('sent', to_send)

        self.sock.send(to_send)


    def recv_data(self, encryption = True):
        """
        Data recieve function
        Gets length of response and then the response
        Makes sure its gotten everything
        """
        try:
            b_len = b''
            while (len(b_len) < len_field):   # Loop to get length in bytes
                b_len += self.sock.recv(len_field - len(b_len))

            msg_len = struct.unpack("!l", b_len)[0]
            if msg_len == b'': print('Seems client disconnected')
            msg = b''
            while (len(msg) < msg_len):   # Loop to recieve the rest of the response
                chunk = self.sock.recv(msg_len - len(msg))
                if not chunk:
                    print('Server disconnected abnormally.')
                    break
                msg += chunk

            if (encryption):  # If encryption is enabled decrypt and log encrypted
                self.logtcp('recv', b_len + msg)   # Log encrypted data
                msg = encrypting.decrypt(msg, self.shared_secret)
                self.logtcp('recv', str(msg_len).encode() + msg)

            return msg
        except ConnectionResetError: return None
        except OSError: pass
        except AttributeError: pass
        except: print(traceback.format_exc())
        
        

    def get_broadcast_address(self, ip, netmask):
        """
        Calculate the broadcast address for the LAN.
        """
        ip_binary = struct.unpack('>I', socket.inet_aton(ip))[0]
        netmask_binary = struct.unpack('>I', socket.inet_aton(netmask))[0]
        broadcast_binary = ip_binary | ~netmask_binary & 0xFFFFFFFF
        return socket.inet_ntoa(struct.pack('>I', broadcast_binary))


    def get_subnet_mask(self):
        # Get the IP address of the default route (external-facing IP)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Connect to a public DNS server (Google's in this case)
            current_ip = s.getsockname()[0]
        
        # Fetch all network interfaces and stats
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        # Iterate over interfaces to find the one matching the current IP
        for interface, addrs_list in addrs.items():
            if stats[interface].isup:  # Check if the interface is up
                for addr in addrs_list:
                    if addr.family == socket.AF_INET and addr.address == current_ip:
                        return addr.netmask, addr.address

        return None  # Return None if no active interface is found


    def search_server(self):
        try:
            search_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            search_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            search_socket.settimeout(3)
            netmask, ip = self.get_subnet_mask()  # Adjust based on your network configuration
            broadcast_address = self.get_broadcast_address(ip, netmask)
            search_socket.sendto(b"SEAR", (broadcast_address, 31026))
            response = None
            i = 0
            while response == None and i < 3:
                response, addr = search_socket.recvfrom(1024)
                time.sleep(0.2)
                i+=1
            response = response.decode().split("|")
            if response[0] == "SERR":
                ip, port = (response[1], response[2])
                return ip, port
        except TimeoutError:
            print("No server found")
        except:
            print(traceback.format_exc())
        