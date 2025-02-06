# 2024 © Idan Hazay
# Import libraries

import struct, traceback, socket

from modules import encrypting
from modules.config import *

class Network:
    def __init__(self, clients, bytes_recieved, bytes_sent, log = False):
        self.log = log
        self.clients = clients
        self.encryption = encrypting.Encryption()
        self.bytes_recieved = bytes_recieved
        self.bytes_sent = bytes_sent

    def logtcp(self, dir, tid, byte_data):
        """
        Loggs the recieved data to console
        """
        if self.log:
            try:
                if (str(byte_data[0]) == "0"):
                    print("")
            except Exception:
                return
            if dir == 'sent':
                print(f'{tid} S LOG:Sent     >>> {byte_data}')
            else:
                print(f'{tid} S LOG:Recieved <<< {byte_data}')


    def send_data(self, sock, tid, bdata):
        """
        Send data to server
        Adds data encryption
        Adds length
        Loggs the encrypted and decrtpted data for readablity
        Checks if encryption is used
        """
        if (self.clients[tid].encryption):
            encrypted_data = self.encryption.encrypt(bdata, self.clients[tid].shared_secret)
            data_len = struct.pack('!l', len(encrypted_data))
            to_send = data_len + encrypted_data
            to_send_decrypted = str(len(bdata)).encode() + bdata
            self.logtcp('sent', tid, to_send)
            self.logtcp('sent', tid, to_send_decrypted)
        else:
            data_len = struct.pack('!l', len(bdata))
            to_send = data_len + bdata
            self.logtcp('sent', tid, to_send)
        try:
            self.bytes_sent[tid] += len(to_send)
            sock.send(to_send)
        except ConnectionResetError:
            pass


    def recv_data(self, sock, tid):
        """
        Data recieve function
        Gets length of response and then the response
        Makes sure its gotten everything
        """
        try:
            b_len = b''
            while (len(b_len) < LEN_FIELD):   # Loop to get length in bytes
                b_len += sock.recv(LEN_FIELD - len(b_len))
            self.bytes_recieved[tid] += len(b_len)
            msg_len = struct.unpack("!l", b_len)[0]
            if msg_len == b'':
                print('Seems client disconnected')
            msg = b''

            while (len(msg) < msg_len):   # Loop to recieve the rest of the response
                chunk = sock.recv(msg_len - len(msg))
                self.bytes_recieved[tid] += len(chunk)
                if not chunk:
                    print('Server disconnected abnormally.')
                    break
                msg += chunk
            # If encryption is enabled decrypt and log encrypted
            if (tid in self.clients and self.clients[tid].encryption):
                self.logtcp('recv', tid, b_len + msg)   # Log encrypted data
                msg = self.encryption.decrypt(msg, self.clients[tid].shared_secret)
                self.logtcp('recv', tid, str(msg_len).encode() + msg)
            return msg

        except ConnectionResetError:
            return None
        except Exception as err:
            print(traceback.format_exc())
    
    @staticmethod
    def dhcp_listen(local_ip, port):
        dhcp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dhcp_socket.bind(("", 31026))
        while True:
            data, addr = dhcp_socket.recvfrom(1024)
            if data.decode() == "SEAR":
                response_message = f"SERR|{local_ip}|{port}"
                dhcp_socket.sendto(response_message.encode(), addr)