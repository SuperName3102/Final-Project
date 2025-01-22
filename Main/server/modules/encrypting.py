# 2024 © Idan Hazay
# Import libraries

import hashlib, os, rsa, struct
from modules.config import *
from Crypto import Random
from Crypto.Cipher import AES
from base64 import b64encode, b64decode


class Encryption:
    def __init__(self):
        self.block_size = AES.block_size

    def encrypt(self, plain_text, key):
        """
        Encryption function
        Adds necessary padding to match block size
        """
        key = hashlib.sha256(key).digest()
        plain_text = self.pad(plain_text)
        iv = Random.new().read(self.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_text = cipher.encrypt(plain_text)
        return b64encode(iv + encrypted_text)

    def decrypt(self, encrypted_text, key):
        """
        Decryption function
        Remove added padding to match block size
        """
        key = hashlib.sha256(key).digest()
        encrypted_text = b64decode(encrypted_text)
        iv = encrypted_text[:self.block_size]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plain_text = cipher.decrypt(encrypted_text[self.block_size:])
        return self.unpad(plain_text)

    def pad(self, plain_text):
        """
        Adds padding to test to match AES block size
        """
        number_of_bytes_to_pad = self.block_size - len(plain_text) % self.block_size
        ascii_string = chr(number_of_bytes_to_pad)
        padding_str = number_of_bytes_to_pad * ascii_string
        padded_plain_text = plain_text + padding_str.encode()
        return padded_plain_text


    def unpad(self, plain_text):
        """
        Removes padding to test to match AES block size
        """
        last_character = plain_text[len(plain_text) - 1:]
        return plain_text[:-ord(last_character)]


    def create_keys(self):
        """
        Creating RSA private and public keys
        For use to transfer shared secret
        Saving keys to file for future use
        """
        self.public_key, self.private_key = rsa.newkeys(1024)   # Gen new keys
        if (not os.path.isfile(f"{os.getcwd()}/keys/public.pem")):
            with open(f"{os.getcwd()}/keys/public.pem", "wb") as f:
                f.write(self.public_key.save_pkcs1("PEM"))
        if (not os.path.isfile(f"{os.getcwd()}/keys/private.pem")):
            with open(f"{os.getcwd()}/keys/private.pem", "wb") as f:
                f.write(self.private_key.save_pkcs1("PEM"))


    def load_keys(self):
        """
        Loading RSA keys from file
        Global vars for use
        """
        with open(f"{os.getcwd()}/keys/public.pem", "rb") as f:
            self.public_key = rsa.PublicKey.load_pkcs1(f.read())
        with open(f"{os.getcwd()}/keys/private.pem", "rb") as f:
            self.private_key = rsa.PrivateKey.load_pkcs1(f.read())


    def send_rsa_key(self, sock, tid):
        """
        Send public RSA key to client
        """
        key_to_send = self.public_key.save_pkcs1()
        key_len = struct.pack("!l", len(key_to_send))

        to_send = key_len + key_to_send
        sock.send(to_send)


    def recv_shared_secret(self, sock, tid):
        """
        Receiving shared secret from client
        Getting the length
        Decrypting with RSA key
        """
        key_len_b = b""
        while (len(key_len_b) < LEN_FIELD):   # Recieve len of key loop
            key_len_b += sock.recv(LEN_FIELD - len(key_len_b))
        key_len = int(struct.unpack("!l", key_len_b)[0])

        key_binary = b""
        while (len(key_binary) < key_len):   # Recieve rest of key according to length
            key_binary += sock.recv(key_len - len(key_binary))
        shared_secret = rsa.decrypt(key_binary, self.private_key)
        return shared_secret


    def rsa_exchange(self, sock, tid):
        self.send_rsa_key(sock, tid)
        return self.recv_shared_secret(sock, tid)

