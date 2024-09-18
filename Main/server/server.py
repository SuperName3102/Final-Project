# 2024 © Idan Hazay
# Import libraries
from modules import client_requests as cr
from modules import encrypting
from modules import validity as v


import socket
import traceback
import time
import threading
import os
import rsa
import struct

# Announce global vars
all_to_die = False  
len_field = 4    
sep = "|" 
clients = {}
chunk_size = 65536

# User handling classes

class Client:
    """
    Client class for handling a client
    """
    def __init__(self, id, user, email, shared_secret, encryption):
        self.id = id
        self.user = user
        self.email = email
        self.shared_secret = shared_secret
        self.encryption = encryption
        self.cwd = f"{os.path.dirname(os.path.abspath(__file__))}/cloud/{self.user}"
        
            

# Files functions
def save_file(file_name, size, sock, tid):
    save_loc = clients[tid].cwd + "/" + file_name
    data = b''
    if not os.path.exists(clients[tid].cwd):
        os.makedirs(clients[tid].cwd)
    
    f = open(save_loc, 'wb')
    while True:
        data = recv_data(sock, tid)
        if not data:
            raise Exception
        if (data[:4] == b"FILD"):
            f.write(data[4:])
        elif (data[:4] == b"FILE"):
            f.write(data[4:])
            break
        data = b''
    print(f"{save_loc} File saved, size: {os.path.getsize(save_loc)}")
    f.close()

# Key exchange 
def create_keys():
    """
    Creating RSA private and public keys
    For use to transfer shared secret
    Saving keys to file for future use
    """
    public_key, private_key = rsa.newkeys(1024)   # Gen new keys
    if(not os.path.isfile(f"{os.path.dirname(os.path.abspath(__file__))}/keys/public.pem")):
        with open(f"{os.path.dirname(os.path.abspath(__file__))}/keys/public.pem", "wb") as f:
            f.write(public_key.save_pkcs1("PEM"))
    if(not os.path.isfile(f"{os.path.dirname(os.path.abspath(__file__))}/keys/private.pem")):
        with open(f"{os.path.dirname(os.path.abspath(__file__))}/keys/private.pem", "wb") as f:
            f.write(private_key.save_pkcs1("PEM"))

def load_keys():
    """
    Loading RSA keys from file
    Global vars for use
    """
    global public_key, private_key
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/keys/public.pem", "rb") as f:
        public_key = rsa.PublicKey.load_pkcs1(f.read())
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/keys/private.pem", "rb") as f:
        private_key = rsa.PrivateKey.load_pkcs1(f.read())

def send_rsa_key(sock, tid):
    """
    Send public RSA key to client
    """
    key_to_send = public_key.save_pkcs1()
    key_len = struct.pack("!l", len(key_to_send))

    to_send = key_len + key_to_send
    logtcp('sent', tid, to_send)
    sock.send(to_send)

def recv_shared_secret(sock, tid):
    """
    Receiving shared secret from client
    Getting the length
    Decrypting with RSA key
    """
    key_len_b = b""
    while(len(key_len_b) < len_field):   # Recieve len of key loop
        key_len_b += sock.recv(len_field - len(key_len_b))
    key_len = int(struct.unpack("!l", key_len_b)[0])

    key_binary = b""
    while(len(key_binary) < key_len):   # Recieve rest of key according to length
        key_binary += sock.recv(key_len - len(key_binary))
    logtcp('recv', tid, key_len_b + key_binary)
    shared_secret = rsa.decrypt(key_binary, private_key)
    return shared_secret

def rsa_exchange(sock, tid):
    send_rsa_key(sock, tid)
    return recv_shared_secret(sock, tid)


# Begin client replies building functions

def protocol_build_reply(request, tid, sock):
    """
    Client request parsing and handling
    Getting the input fields
    Checking the action code
    Performing actions for each different code
    Returning the reply to the client
    """
    global clients
    fields = request.decode()   # Parse the reply and aplit it according to the protocol seperator
    fields = fields.split(sep)
    code = fields[0]

    # Checking each indevidual code
    if code == 'EXIT':   # Client requests disconnection
        reply = 'EXTR'
        clients[tid].user = "dead"
    
    elif (code == "LOGN"):   # Client requests login
        cred = fields[1]
        password = fields[2]
        print(fields[1:])
        if (v.is_empty(fields[1:])):
            return  f"ERRR{sep}101{sep}Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return  f"ERRR{sep}102{sep}Invalid chars used"

        if (cr.login_validation(cred, password)):
            if(not cr.verified(cred)):
                reply = f"ERRR{sep}010{sep}User not verified"
            else:
                user_dict = cr.get_user_data(cred)
                username = user_dict["username"]
                email = user_dict["email"]
                clients[tid].user = username
                clients[tid].email = email
                clients[tid].cwd = f"{os.path.dirname(os.path.abspath(__file__))}/cloud/{username}"
                reply = f"LOGS{sep}{email}{sep}{username}{sep}{password}"
        else:
            reply = f"ERRR{sep}004{sep}Invalid credentials"
    
    elif (code == "SIGU"):   # Client requests signup
        email = fields[1]
        username = fields[2]
        password = fields[3]
        confirm_password = fields[4]
        
        if (v.is_empty(fields[1:])):
            return  f"ERRR{sep}101{sep}Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return  f"ERRR{sep}102{sep}Invalid chars used"
        elif (not v.is_valid_email(email)):
            return  f"ERRR{sep}103{sep}Invalid email address"
        elif (not v.is_valid_username(username)):
            return  f"ERRR{sep}104{sep}Invalid username\nUsername has to be at least 4 long and contain only chars and numbers"
        elif (not v.is_valid_password(password)):
            return  f"ERRR{sep}105{sep}Password does not meet requirements\nhas to be at least 8 long and contain at least 1 upper case and number"
        elif (password != confirm_password):
            return  f"ERRR{sep}106{sep}Passwords do not match"
        
        
        if (cr.user_exists(username)):
            reply = f"ERRR{sep}005{sep}Username already registered"
        elif(cr.email_registered(email)):
            reply = f"ERRR{sep}006{sep}Email address already registered"
        else:
            user_details = [email, username, password]
            cr.signup_user(user_details)
            cr.send_verification(email)
            reply = f"SIGS{sep}{email}{sep}{username}{sep}{password}"
    
    elif (code == "FOPS"):   # Client requests password reset code
        email = fields[1]
        if (v.is_empty(fields[1:])):
            return  f"ERRR{sep}101{sep}Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return  f"ERRR{sep}102{sep}Invalid chars used"
        elif (not v.is_valid_email(email)):
            return  f"ERRR{sep}103{sep}Invalid email address"
        
        if (cr.email_registered(email)):
            if(not cr.verified(email)):
                reply = f"ERRR{sep}010{sep}User not verified"
            else:
                cr.send_reset_mail(email)
                reply = f"FOPR{sep}{email}"
        else:
            reply = f"ERRR{sep}007{sep}Email is not registered"
    
    elif (code == "PASR"):   # Client requests password reset
        email = fields[1]
        code = fields[2]
        new_password = fields[3]
        confirm_new_password = fields[3]
        
        if (v.is_empty(fields[1:])):
            return  f"ERRR{sep}101{sep}Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return  f"ERRR{sep}102{sep}Invalid chars used"
        elif (not v.is_valid_password(new_password)):
            return  f"ERRR{sep}105{sep}Password does not meet requirements\nhas to be at least 8 long and contain at least 1 upper case and number"
        elif (new_password != confirm_new_password):
            return  f"ERRR{sep}106{sep}Passwords do not match"
        
        res = cr.check_code(email, code)
        if (res == "ok"):
            cr.change_password(email, new_password)
            clients[tid].user = "guest"
            reply = f"PASS{sep}{email}{sep}{new_password}"
        elif(res == "code"):
            reply = f"ERRR{sep}008{sep}Code not matching try again"
        else:
            reply = f"ERRR{sep}009{sep}Code validation time ran out"
    
    elif(code == "LOGU"):   # Client requests logout
        clients[tid].user = "guest"
        reply = "LUGR"
    
    elif(code == "SVER"):   # Client requests account verification code
        email = fields[1]
        
        if (v.is_empty(fields[1:])):
            return  f"ERRR{sep}101{sep}Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return  f"ERRR{sep}102{sep}Invalid chars used"
        elif (not v.is_valid_email(email)):
            return  f"ERRR{sep}103{sep}Invalid email address"
        
        if (cr.email_registered(email)):
            if(cr.verified(email)):
                reply = f"ERRR{sep}011{sep}Already verified"
            else:
                cr.send_verification(email)
                reply = f"VERS{sep}{email}"
        else:
            reply = f"ERRR{sep}007{sep}Email is not registered"
    
    elif(code == "VERC"):   # Client requests account verification
        email = fields[1]
        code = fields[2]
        
        if (v.is_empty(fields[1:])):
            return  f"ERRR{sep}101{sep}Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return  f"ERRR{sep}102{sep}Invalid chars used"
        elif (not v.is_valid_email(email)):
            return  f"ERRR{sep}103{sep}Invalid email address"
        
        if (cr.email_registered(email)):
            res = cr.check_code(email, code)
            if (res == "ok"):
                cr.verify_user(email)
                reply = f"VERR{sep}{email}"
            elif(res == "code"):
                reply = f"ERRR{sep}008{sep}Code not matching try again"
            else:
                reply = f"ERRR{sep}009{sep}Code validation time ran out"
        else:
            reply = f"ERRR{sep}007{sep}Email is not registered"
    
    elif(code == "DELU"):   # Client requests user deletion
        email = fields[1]
        
        if (v.is_empty(fields[1:])):
            return  f"ERRR{sep}101{sep}Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return  f"ERRR{sep}102{sep}Invalid chars used"
        elif (clients[tid].email !=email):
            return  f"ERRR{sep}013{sep}Can't delete this user"
        
        if(cr.user_exists(email)):
            cr.delete_user(email)
            clients[tid].user = "guest"
            reply = f"DELR{sep}{email}"
        else:
            reply = f"ERRR{sep}004{sep}Invalid credentials"
    
    elif (code == "FILS"):
        file_name = fields[2]
        size = fields[3]
        try:
            save_file(file_name, size, sock, tid)
            reply = f"FILR{sep}{file_name}{sep}was saved succefully"
        except Exception:
            print(traceback.format_exc())
            reply = f"ERRR{sep}012{sep}File didnt upload correctly"
    
    elif (code == "GETP"):
        reply = "PATH"
        files = cr.get_files(clients[tid].cwd)
        for file in files:
            reply += f"{sep}{file}"
    
    elif (code == "GETD"):
        reply = "PATD"
        directories = cr.get_directories(clients[tid].cwd)
        for directory in directories:
            reply += f"{sep}{directory}"
    
    elif (code == "MOVD"):
        dir = fields[1]
        new_cwd = (clients[tid].cwd + "/" + dir)
        if (os.path.isdir(new_cwd)):
            main_path = f"{os.path.dirname(os.path.abspath(__file__))}/cloud/{clients[tid].user}"
            if not (cr.is_subpath(main_path, new_cwd)):
                reply = f"ERRR{sep}014{sep}Invalid directory"
            else:
                clients[tid].cwd = new_cwd
                reply = f"MOVR{sep}{dir}{sep}moved succesfully"
        else:
            reply = f"ERRR{sep}014{sep}Invalid directory"
    
    else:
        reply = f"ERRR{sep}002{sep}Code not supported"
        fields = ''
    
    return reply

def handle_request(request, tid, sock):
    """
    Getting client request and parsing it
    If some error occured or no response return general error
    """
    try:
        to_send = protocol_build_reply(request, tid, sock).encode()
    except Exception as err:
        print(traceback.format_exc())
        to_send = f"ERRR{sep}001{sep}General error"
        to_send = to_send.encode()
    return to_send, False



# Begin data handling and processing functions 

def logtcp(dir, tid, byte_data):
    """
    Loggs the recieved data to console
    """
    try:
        if (str(byte_data[0]) == "0"):
            print("")
    except AttributeError:
        return
    except Exception:
        return
    if dir == 'sent':
        print(f'{tid} S LOG:Sent     >>> {byte_data}')
    else:
        print(f'{tid} S LOG:Recieved <<< {byte_data}')

def send_data(sock, tid, bdata):
    """
    Send data to server
    Adds data encryption
    Adds length
    Loggs the encrypted and decrtpted data for readablity
    Checks if encryption is used
    """
    if(clients[tid].encryption):
        encrypted_data = encrypting.encrypt(bdata, clients[tid].shared_secret)
        data_len = struct.pack('!l', len(encrypted_data))
        to_send = data_len + encrypted_data
        to_send_decrypted = str(len(bdata)).encode() + bdata
        logtcp('sent', tid, to_send)
        logtcp('sent', tid, to_send_decrypted)
    else:
        data_len = struct.pack('!l', len(bdata))
        to_send = data_len + bdata
        logtcp('sent', tid, to_send)
    
    sock.send(to_send)

def recv_data(sock, tid):
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
        if msg_len == b'':
            print('Seems client disconnected')
        msg = b''
        
        while (len(msg) < msg_len):   # Loop to recieve the rest of the response
            chunk = sock.recv(msg_len - len(msg))
            if not chunk:
                print('Server disconnected abnormally.')
                break
            msg += chunk
        if(tid in clients and clients[tid].encryption): # If encryption is enabled decrypt and log encrypted
            logtcp('recv', tid, b_len + msg)   # Log encrypted data
            msg = encrypting.decrypt(msg, clients[tid].shared_secret)
        return msg
    
    except Exception as err:
        print(traceback.format_exc())



# Main function and client handling, start of code

def handle_client(sock, tid, addr):
    """
    Client handling function
    Sends RSA public key and recieves shared secret for secure connection
    """
    global all_to_die
    global clients
    try:
        finish = False
        print(f'New Client number {tid} from {addr}')
        start = recv_data(sock, tid)
        code = start.split(b"|")[0]
        clients[tid] = Client(tid, "guest", "guest", None, False)   # Setting client state
        if (code == b"RSAR"):
            shared_secret = rsa_exchange(sock, tid)
        if(shared_secret == ""):
            return

        clients[tid].shared_secret = shared_secret
        clients[tid].encryption = True
    except Exception:
        print(traceback.format_exc())
        print(f'Client {tid} connection error')   # Releasing clienk and closing socket
        if (tid in clients):
            clients[tid].user = "dead"
        sock.close()
        return
    while not finish:   # Main client loop
        if all_to_die:
            print('will close due to main server issue')
            break
        try:
            entire_data = recv_data(sock, tid)   # Recieving data and  handling client
            logtcp('recv', tid, entire_data)
            to_send, finish = handle_request(entire_data, tid, sock)
            if to_send != '':
                send_data(sock, tid, to_send)
            if finish:
                time.sleep(1)
                break
        except socket.error as err:
            print(f'Socket Error exit client loop: err:  {err}')
            break
        except Exception as err:
            print(f'General Error %s exit client loop: {err}')
            print(traceback.format_exc())
            break
    print(f'Client {tid} Exit')   # Releasing clienk and closing socket
    clients[tid].user = "dead"
    sock.close()


def main(addr):
    """
    Main function
    Listens for clients from any addr
    Creates threads to handle each user
    Handles every user seperately
    """
    global all_to_die

    threads = []
    srv_sock = socket.socket()
    srv_sock.bind(addr)
    srv_sock.listen(20)
    
    print(f"Server listening on {addr}")
    srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    i = 1

    create_keys()
    load_keys()
    
    print('Main thread: before accepting ...\n')
    while True:
        cli_sock, addr = srv_sock.accept()
        t = threading.Thread(target=handle_client, args=(cli_sock, str(i), addr))   # Accepting client and assigning id
        t.start()
        i += 1
        threads.append(t)
        if i > 100000000:
            print('\nMain thread: going down for maintenance')
            break

    all_to_die = True
    print('Main thread: waiting to all clints to die')
    for t in threads:
        t.join()
    srv_sock.close()
    print('Bye ..')

if __name__ == '__main__':   # Run main
    cr.main()
    main(("0.0.0.0", 31026))
