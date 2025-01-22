# 2024 © Idan Hazay
# Import libraries

from modules.config import *
import os, rsa, struct

# Key exchange
class KeyExchange():
    def __init__(self, network):
        self.network = network
    
    def rsa_exchange(self):
        try:
            self.network.send_data_wrap(b"RSAR", False)
            s_public_key = self.recv_rsa_key()
            shared_secret = self.send_shared_secret(s_public_key)
            return shared_secret
        except:
            print(traceback.format_exc())


    def recv_rsa_key(self):
        """
        RSA key recieve from server
        Gets the length of the key in binary
        Gets the useable key and saves it as global var for future use
        """
        key_len_b = b""
        while (len(key_len_b) < len_field):   # Recieve the length of the key
            key_len_b += self.network.sock.recv(len_field - len(key_len_b))
        key_len = int(struct.unpack("!l", key_len_b)[0])

        key_binary = b""
        while (len(key_binary) < key_len):   # Recieve the key according to its length
            key_binary += self.network.sock.recv(key_len - len(key_binary))

        s_public_key = rsa.PublicKey.load_pkcs1(key_binary)   # Save the key
        return s_public_key


    def send_shared_secret(self, s_public_key):
        """
        Create and send the shared secret
        to server via secure rsa connection
        """
        shared_secret = os.urandom(16)
        key_to_send = rsa.encrypt(shared_secret, s_public_key)
        key_len = struct.pack("!l", len(key_to_send))
        to_send = key_len + key_to_send
        self.network.sock.send(to_send)
        return shared_secret