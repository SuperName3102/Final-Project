# 2024 © Idan Hazay
# Import libraries
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
from base64 import b64encode, b64decode


# Begin encryption related functions
block_size = AES.block_size


def encrypt(plain_text, key):
    """
    Encryption function
    Adds necessary padding to match block size
    """
    key = hashlib.sha256(key).digest()
    plain_text = pad(plain_text)
    iv = Random.new().read(block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_text = cipher.encrypt(plain_text)
    return b64encode(iv + encrypted_text)

def decrypt(encrypted_text, key):
    """
    Decryption function
    Remove added padding to match block size
    """
    key = hashlib.sha256(key).digest()
    encrypted_text = b64decode(encrypted_text)
    iv = encrypted_text[:block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plain_text = cipher.decrypt(encrypted_text[block_size:])
    return unpad(plain_text)

def pad(plain_text):
    """
    Adds padding to test to match AES block size
    """
    number_of_bytes_to_pad = block_size - len(plain_text) % block_size
    ascii_string = chr(number_of_bytes_to_pad)
    padding_str = number_of_bytes_to_pad * ascii_string
    padded_plain_text = plain_text + padding_str.encode()
    return padded_plain_text


def unpad(plain_text):
    """
    Removes padding to test to match AES block size
    """
    last_character = plain_text[len(plain_text) - 1:]
    return plain_text[:-ord(last_character)]

