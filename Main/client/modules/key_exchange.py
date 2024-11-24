# 2024 © Idan Hazay

from modules.global_vars import *
from modules.networking import *
import os, rsa, struct

# Key exchange
def rsa_exchange(sock):
    try:
        send_data_wrap(b"RSAR", False)
        s_public_key = recv_rsa_key(sock)
        shared_secret = send_shared_secret(s_public_key, sock)
        return shared_secret
    except:
        print(traceback.format_exc())


def recv_rsa_key(sock):
    """
    RSA key recieve from server
    Gets the length of the key in binary
    Gets the useable key and saves it as global var for future use
    """
    key_len_b = b""
    while (len(key_len_b) < len_field):   # Recieve the length of the key
        key_len_b += sock.recv(len_field - len(key_len_b))
    key_len = int(struct.unpack("!l", key_len_b)[0])

    key_binary = b""
    while (len(key_binary) < key_len):   # Recieve the key according to its length
        key_binary += sock.recv(key_len - len(key_binary))

    s_public_key = rsa.PublicKey.load_pkcs1(key_binary)   # Save the key
    return s_public_key


def send_shared_secret(s_public_key, sock):
    """
    Create and send the shared secret
    to server via secure rsa connection
    """
    shared_secret = os.urandom(16)
    key_to_send = rsa.encrypt(shared_secret, s_public_key)
    key_len = struct.pack("!l", len(key_to_send))
    to_send = key_len + key_to_send
    sock.send(to_send)
    return shared_secret