# 2024 © Idan Hazay

import modules.encrypting as encrypting
from modules.config import *
import struct 

log = False
shared_secret = ""
sock = ""

def set_sock(socket):
    global sock
    sock = socket

def set_secret(secret):
    global shared_secret
    shared_secret = secret

def logtcp(dir, byte_data):
    """
    Loggs the recieved data to console
    """
    if log:
        try:
            if (str(byte_data[0]) == "0"):print("")
        except AttributeError:
            return
        if dir == 'sent':   # Sen/recieved labels
            print(f'C LOG:Sent     >>>{byte_data}')
        else:
            print(f'C LOG:Recieved <<<{byte_data}')


def send_data_wrap(bdata, encryption):
    """
    Send data to server
    Adds data encryption
    Adds length
    Loggs the encrypted and decrtpted data for readablity
    Checks if encryption is used
    """
    if (encryption):
        encrypted_data = encrypting.encrypt(bdata, shared_secret)
        data_len = struct.pack('!l', len(encrypted_data))
        to_send = data_len + encrypted_data
        to_send_decrypted = str(len(bdata)).encode() + bdata
        logtcp('sent', to_send)
        logtcp('sent', to_send_decrypted)
    else:
        data_len = struct.pack('!l', len(bdata))
        to_send = data_len + bdata
        logtcp('sent', to_send)
 
    sock.send(to_send)


def recv_data(encryption = True):
    """
    Data recieve function
    Gets length of response and then the response
    Makes sure its gotten everything
    """
    try:
        b_len = b''
        while (len(b_len) < len_field):   # Loop to get length in bytes
            b_len += sock.recv(len_field - len(b_len))

        msg_len = struct.unpack("!l", b_len)[0]
        if msg_len == b'': print('Seems client disconnected')
        msg = b''
        while (len(msg) < msg_len):   # Loop to recieve the rest of the response
            chunk = sock.recv(msg_len - len(msg))
            if not chunk:
                print('Server disconnected abnormally.')
                break
            msg += chunk

        if (encryption):  # If encryption is enabled decrypt and log encrypted
            logtcp('recv', b_len + msg)   # Log encrypted data
            msg = encrypting.decrypt(msg, shared_secret)
            logtcp('recv', str(msg_len).encode() + msg)

        return msg
    except ConnectionResetError: return None
    except OSError: pass
    except AttributeError: pass
    except: print(traceback.format_exc())