# 2024 © Idan Hazay
# Import libraries

from modules import client_requests as cr
from modules import encrypting
from modules import validity as v
from modules.errors import Errors
from modules.limits import Limits, LimitExceeded

import socket
import traceback
import time
import threading
import os
import rsa
import struct
import shutil
from filelock import FileLock

# Announce global vars
all_to_die = False
len_field = 4
sep = "|"
clients = {}
chunk_size = 65536
cloud_path = f"{os.path.dirname(os.path.abspath(__file__))}\\cloud"
user_icons_path = f"{os.path.dirname(os.path.abspath(__file__))}\\user icons"
log = False


# User handling classes

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


def save_file(save_path, sock, tid):
    data = b''
    lock_path = f"{save_path}.lock"
    lock = FileLock(lock_path)
    total_size = 0
    start = time.time()
    bytes_written = 0
    try:
        with lock:
            with open(save_path, 'wb') as f:
                while True:
                    data = recv_data(sock, tid)
                    if not data:
                        raise Exception
                    total_size += len(data) - 4
                    if (total_size > Limits(clients[tid].subscription_level).max_file_size * 1_000_000):
                        raise LimitExceeded("File exceeded size limit")

                    current_time = time.time()
                    elapsed_time = current_time - start
                    if elapsed_time >= 1.0:
                        start = current_time
                        bytes_written = 0

                    if (data[:4] == b"FILD"):
                        f.write(data[4:])
                        bytes_written += len(data) - 4
                    elif (data[:4] == b"FILE"):
                        f.write(data[4:])
                        bytes_written += len(data) - 4
                        break
                    else:
                        raise Exception

                    if bytes_written >= Limits(clients[tid].subscription_level).max_upload_speed * 1_000_000:
                        time_to_wait = 1.0 - elapsed_time
                        if time_to_wait > 0:
                            time.sleep(time_to_wait)
                    data = b''
                f.flush()
    except LimitExceeded as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        if os.path.exists(lock_path):
            os.remove(lock_path)
        raise


def throw_file(sock, tid):
    data = b''
    while True:
        data = recv_data(sock, tid)
        if not data:
            raise Exception
        if (data[:4] == b"FILD"):
            pass
        elif (data[:4] == b"FILE"):
            break
        else:
            raise Exception
        data = b''


def send_file_data(file_path, sock, tid):
    size = os.path.getsize(file_path)
    left = size % chunk_size

    lock_path = f"{file_path}.lock"
    lock = FileLock(lock_path)

    start = time.time()
    bytes_sent = 0
    try:
        with lock:
            with open(file_path, 'rb+') as f:
                for i in range(size//chunk_size):
                    data = f.read(chunk_size)

                    current_time = time.time()
                    elapsed_time = current_time - start

                    if elapsed_time >= 1.0:
                        start = current_time
                        bytes_sent = 0

                    send_data(sock, tid, b"RILD" + data)
                    bytes_sent += len(data)
                    if bytes_sent >= Limits(clients[tid].subscription_level).max_download_speed * 1_000_000:
                        time_to_wait = 1.0 - elapsed_time
                        if time_to_wait > 0:
                            time.sleep(time_to_wait)

                data = f.read(left)
                if (data != b""):
                    send_data(sock, tid, b'RILE' + data)

    except:
        if os.path.exists(lock_path):
            os.remove(lock_path)
        raise


def get_user_storage(username):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(cloud_path + "\\" + username):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # Skip if the file is broken or inaccessible
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def is_guest(tid):
    return clients[tid].user == "guest"

# Key exchange


def create_keys():
    """
    Creating RSA private and public keys
    For use to transfer shared secret
    Saving keys to file for future use
    """
    public_key, private_key = rsa.newkeys(1024)   # Gen new keys
    if (not os.path.isfile(f"{os.path.dirname(os.path.abspath(__file__))}/keys/public.pem")):
        with open(f"{os.path.dirname(os.path.abspath(__file__))}/keys/public.pem", "wb") as f:
            f.write(public_key.save_pkcs1("PEM"))
    if (not os.path.isfile(f"{os.path.dirname(os.path.abspath(__file__))}/keys/private.pem")):
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
    while (len(key_len_b) < len_field):   # Recieve len of key loop
        key_len_b += sock.recv(len_field - len(key_len_b))
    key_len = int(struct.unpack("!l", key_len_b)[0])

    key_binary = b""
    while (len(key_binary) < key_len):   # Recieve rest of key according to length
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
    if request is None:
        return None
    # Parse the reply and aplit it according to the protocol seperator
    fields = request.decode()
    fields = fields.split("|")
    code = fields[0]

    # Checking each indevidual code
    if code == 'EXIT':   # Client requests disconnection
        reply = 'EXTR'
        clients[tid].user = "dead"

    elif (code == "LOGN"):   # Client requests login
        cred = fields[1]
        password = fields[2]
        if (v.is_empty(fields[1:])):
            return f"ERRR|101|Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return f"ERRR|102|Invalid chars used"

        if (cr.login_validation(cred, password)):
            if (not cr.verified(cred)):
                reply = Errors.NOT_VERIFIED.value

            else:
                user_dict = cr.get_user_data(cred)
                username = user_dict["username"]
                email = user_dict["email"]
                clients[tid].user = username
                clients[tid].email = email
                clients[tid].cwd = f"{cloud_path}\\{username}"
                clients[tid].subscription_level = user_dict["subscription_level"]
                clients[tid].admin_level = user_dict["admin_level"]
                reply = f"LOGS|{email}|{username}|{password}|{
                    int(clients[tid].subscription_level)}"
        else:
            reply = Errors.LOGIN_DETAILS.value

    elif (code == "SIGU"):   # Client requests signup
        email = fields[1]
        username = fields[2]
        password = fields[3]
        confirm_password = fields[4]

        if (v.is_empty(fields[1:])):
            return f"ERRR|101|Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return f"ERRR|102|Invalid chars used"
        elif (not v.is_valid_email(email)):
            return f"ERRR|103|Invalid email address"
        elif (not v.is_valid_username(username) or username == "guest"):
            return f"ERRR|104|Invalid username\nUsername has to be at least 4 long and contain only chars and numbers"
        elif (not v.is_valid_password(password)):
            return f"ERRR|105|Password does not meet requirements\nhas to be at least 8 long and contain at least 1 upper case and number"
        elif (password != confirm_password):
            return f"ERRR|106|Passwords do not match"

        if (cr.user_exists(username)):
            reply = Errors.USER_REGISTERED.value
        elif (cr.email_registered(email)):
            reply = Errors.EMAIL_REGISTERED.value
        else:
            user_details = [email, username, password]
            cr.signup_user(user_details)
            cr.send_verification(email)
            reply = f"SIGS|{email}|{username}|{password}"

    elif (code == "FOPS"):   # Client requests password reset code
        email = fields[1]
        if (v.is_empty(fields[1:])):
            return f"ERRR|101|Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return f"ERRR|102|Invalid chars used"
        elif (not v.is_valid_email(email)):
            return f"ERRR|103|Invalid email address"

        if (cr.email_registered(email)):
            if (not cr.verified(email)):
                reply = Errors.NOT_VERIFIED.value
            else:
                cr.send_reset_mail(email)
                reply = f"FOPR|{email}"
        else:
            reply = Errors.EMAIL_NOT_REGISTERED.value

    elif (code == "PASR"):   # Client requests password reset
        email = fields[1]
        code = fields[2]
        new_password = fields[3]
        confirm_new_password = fields[4]

        if (v.is_empty(fields[1:])):
            return f"ERRR|101|Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return f"ERRR|102|Invalid chars used"
        elif (not v.is_valid_password(new_password)):
            return f"ERRR|105|Password does not meet requirements\nhas to be at least 8 long and contain at least 1 upper case and number"
        elif (new_password != confirm_new_password):
            return f"ERRR|106|Passwords do not match"

        res = cr.check_code(email, code)
        if (res == "ok"):
            cr.change_password(email, new_password)
            clients[tid].user = "guest"
            reply = f"PASS|{email}|{new_password}"
        elif (res == "code"):
            reply = Errors.NOT_MATCHING_CODE.value
        else:
            reply = Errors.CODE_EXPIRED.value

    elif (code == "LOGU"):   # Client requests logout
        clients[tid].user = "guest"
        clients[tid].email = "guest"
        clients[tid].cwd = f"{cloud_path}\\guest"
        clients[tid].subscription_level = 0
        clients[tid].admin_level = 0
        reply = "LUGR"

    elif (code == "SVER"):   # Client requests account verification code
        email = fields[1]

        if (v.is_empty(fields[1:])):
            return f"ERRR|101|Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return f"ERRR|102|Invalid chars used"
        elif (not v.is_valid_email(email)):
            return f"ERRR|103|Invalid email address"

        if (cr.email_registered(email)):
            if (cr.verified(email)):
                reply = Errors.ALREADY_VERIFIED.value
            else:
                cr.send_verification(email)
                reply = f"VERS|{email}"
        else:
            reply = Errors.EMAIL_NOT_REGISTERED.value

    elif (code == "VERC"):   # Client requests account verification
        email = fields[1]
        code = fields[2]

        if (v.is_empty(fields[1:])):
            return f"ERRR|101|Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return f"ERRR|102|Invalid chars used"
        elif (not v.is_valid_email(email)):
            return f"ERRR|103|Invalid email address"

        if (cr.email_registered(email)):
            res = cr.check_code(email, code)
            if (res == "ok"):
                cr.verify_user(email)
                cr.send_welcome_mail(email)
                reply = f"VERR|{email}"
            elif (res == "code"):
                reply = Errors.NOT_MATCHING_CODE.value
            else:
                reply = Errors.CODE_EXPIRED.value
        else:
            reply = Errors.EMAIL_NOT_REGISTERED.value

    elif (code == "DELU"):   # Client requests user deletion
        email = fields[1]

        if (v.is_empty(fields[1:])):
            return f"ERRR|101|Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return f"ERRR|102|Invalid chars used"
        elif (clients[tid].email != email):
            return Errors.NO_DELETE_PERMS.value

        if (cr.user_exists(email)):
            cr.delete_user(email)
            shutil.rmtree(cloud_path + "\\" + clients[tid].user)
            clients[tid].user = "guest"
            reply = f"DELR|{email}"
        else:
            reply = Errors.LOGIN_DETAILS.value

    elif (code == "FILS"):
        file_name = fields[1]
        save_loc = clients[tid].cwd + "/" + file_name
        try:
            if(is_guest(tid)):
                throw_file(sock, tid)
                reply = Errors.NO_PREMISSION.value
            elif (get_user_storage(clients[tid].user) > Limits(clients[tid].subscription_level).max_storage * 1_000_000):
                throw_file(sock, tid)
                reply = Errors.MAX_STORAGE.value
            elif os.path.isfile(save_loc):
                throw_file(sock, tid)
                reply = Errors.FILE_EXISTS.value

            else:
                if not os.path.exists(clients[tid].cwd):
                    os.makedirs(clients[tid].cwd)
                try:
                    save_file(save_loc, sock, tid)
                    reply = f"FILR|{file_name}|was saved succefully"
                except LimitExceeded:
                    throw_file(sock, tid)
                    reply = Errors.SIZE_LIMIT.value + " " + \
                        str(Limits(
                            clients[tid].subscription_level).max_file_size) + " MB"
        except Exception:
            print(traceback.format_exc())
            throw_file(sock, tid)
            reply = Errors.FILE_UPLOAD.value

    elif (code == "GETP"):
        if (len(fields) == 2):
            search_filter = fields[1]
            if (v.is_empty(fields[1:])):
                return f"ERRR|101|Cannot have an empty field"
            elif (v.check_illegal_chars(fields[1:])):
                return f"ERRR|102|Invalid chars used"
            files = cr.get_files(clients[tid].cwd, search_filter)
        else:
            files = cr.get_files(clients[tid].cwd)
        reply = "PATH"
        for file in files:
            reply += f"|{file}"

    elif (code == "GETD"):
        if (len(fields) == 2):
            search_filter = fields[1]
            if (v.is_empty(fields[1:])):
                return f"ERRR|101|Cannot have an empty field"
            elif (v.check_illegal_chars(fields[1:])):
                return f"ERRR|102|Invalid chars used"
            directories = cr.get_directories(clients[tid].cwd, search_filter)
        else:
            directories = cr.get_directories(clients[tid].cwd)

        reply = "PATD"
        for directory in directories:
            reply += f"|{directory}"

    elif (code == "MOVD"):
        dir = fields[1]
        if (dir == "/.."):
            new_cwd = ("\\".join(clients[tid].cwd.split("\\")[:-1]))
        else:
            new_cwd = (clients[tid].cwd + "\\" + dir)
        if (os.path.isdir(new_cwd)):
            main_path = f"{cloud_path}\\{clients[tid].user}"
            if (not (cr.is_subpath(main_path, new_cwd))):
                reply = Errors.INVALID_DIRECTORY.value
            else:
                clients[tid].cwd = new_cwd
                reply = f"MOVR|{new_cwd.split(
                    "cloud")[1][1:]}|moved succesfully"
        else:
            reply = Errors.INVALID_DIRECTORY.value

    elif (code == "DOWN"):
        file_name = fields[1]
        file_path = os.path.join(clients[tid].cwd, file_name)
        if (not os.path.isfile(file_path)):
            reply = Errors.FILE_NOT_FOUND.value
        else:
            try:
                send_file_data(file_path, sock, tid)
                reply = f"DOWR|{file_name}|was downloaded"
            except Exception:
                reply = Errors.FILE_DOWNLOAD.value

    elif (code == "NEWF"):
        folder_name = fields[1]
        folder_path = clients[tid].cwd + "\\" + folder_name
        if (not os.path.isdir(folder_path)):
            os.makedirs(folder_path, exist_ok=True)
            reply = f"NEFR|{folder_name}|was created"
        else:
            reply = Errors.FOLDER_EXISTS.value

    elif (code == "RENA"):
        name = fields[1]
        new_name = fields[2]

        path = clients[tid].cwd + "\\" + name
        new_path = clients[tid].cwd + "\\" + new_name
        if (not os.path.isfile(path) and not os.path.isdir(path)):
            reply = Errors.FILE_NOT_FOUND.value
        elif (os.path.exists(new_path)):
            reply = Errors.EXISTS.value
        else:
            os.rename(path, new_path)
            reply = f"RENR|{name}|{new_name}|File renamed succefully"

    elif (code == "GICO"):
        if (os.path.isfile(os.path.join(user_icons_path, clients[tid].user + ".ico"))):
            send_file_data(os.path.join(user_icons_path,
                           clients[tid].user + ".ico"), sock, tid)
        else:
            send_file_data(os.path.join(
                user_icons_path, "guest.ico"), sock, tid)
        reply = f"GICR|Sent use profile picture"

    elif (code == "ICOS"):
        file_name = fields[1]
        try:
            save_path = os.path.join(
                user_icons_path, clients[tid].user + ".ico")
            try:
                save_file(save_path, sock, tid)
                reply = f"ICOR|Profile icon was uploaded succefully"
            except LimitExceeded:
                throw_file(sock, tid)
                reply = Errors.SIZE_LIMIT.value + " " +\
                    str(Limits(
                        clients[tid].subscription_level).max_file_size) + " MB"

        except Exception:
            print(traceback.format_exc())
            throw_file(sock, tid)
            reply = Errors.FILE_UPLOAD.value

    elif code == 'DELF':
        name = fields[1]
        path = clients[tid].cwd + "\\" + name
        if not os.path.exists(path):
            reply = Errors.FILE_NOT_FOUND.value
        elif os.path.isfile(path):
            os.remove(path)
            reply = f"DLFR|{name}|was deleted!"
        elif os.path.isdir(path):
            shutil.rmtree(path)
            reply = f"DFFR|{name}|was deleted!"

    elif code == "SUBL":
        level = fields[1]
        if (level == clients[tid].subscription_level):
            reply = Errors.SAME_LEVEL.value
        elif (int(level) < 0 or int(level) > 3):
            reply = Errors.INVALID_LEVEL.value
        else:
            cr.change_level(clients[tid].email, int(level))
            clients[tid].subscription_level = int(level)
            reply = f"SUBR|{level}|Subscription level updated"

    elif code == "GEUS":
        used_storage = get_user_storage(clients[tid].user)
        reply = f"GEUR|{used_storage}"

    elif code == "CHUN":
        new_username = fields[1]
        if (v.is_empty(fields[1:])):
            return f"ERRR|101|Cannot have an empty field"
        elif (v.check_illegal_chars(fields[1:])):
            return f"ERRR|102|Invalid chars used"
        elif (not v.is_valid_username(new_username) or new_username == "guest"):
            return f"ERRR|104|Invalid username\nUsername has to be at least 4 long and contain only chars and numbers"
        elif (cr.user_exists(new_username)):
            reply = Errors.USER_REGISTERED.value
        else:
            os.rename(cloud_path + "\\" + clients[tid].user, cloud_path + "\\" + new_username)
            cr.change_username(clients[tid].user, new_username)
            clients[tid].cwd = cloud_path + "\\" + new_username
            clients[tid].user = new_username
            reply = f"CHUR|{new_username}|Changed username"
    
    elif code == "VIEW":
        file_name = fields[1]
        file_path = os.path.join(clients[tid].cwd, file_name)
        if (not os.path.isfile(file_path)):
            reply = Errors.FILE_NOT_FOUND.value
        elif (os.path.getsize(file_path) > 10_000_000):
            reply = Errors.PREVIEW_SIZE.value
        else:
            try:
                send_file_data(file_path, sock, tid)
                reply = f"VIER|{file_name}|was viewed"
            except Exception:
                reply = Errors.FILE_DOWNLOAD.value

    else:
        reply = Errors.UNKNOWN.value
        fields = ''

    return reply


def handle_request(request, tid, sock):
    """
    Getting client request and parsing it
    If some error occured or no response return general error
    """
    client_exit = False
    try:
        to_send = protocol_build_reply(request, tid, sock)
        if to_send == None:
            return None, True
        to_send = to_send.encode()
        if (to_send == b"EXTR"):
            client_exit = True
    except Exception as err:
        print(traceback.format_exc())
        to_send = Errors.GENERAL.value
        to_send = to_send.encode()
    return to_send, client_exit


# Begin data handling and processing functions

def logtcp(dir, tid, byte_data):
    """
    Loggs the recieved data to console
    """
    if log:
        try:
            if (str(byte_data[0]) == "0"):
                print("")
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
    if (clients[tid].encryption):
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
    try:
        sock.send(to_send)
    except ConnectionResetError:
        pass


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
        # If encryption is enabled decrypt and log encrypted
        if (tid in clients and clients[tid].encryption):
            logtcp('recv', tid, b_len + msg)   # Log encrypted data
            msg = encrypting.decrypt(msg, clients[tid].shared_secret)
            logtcp('recv', tid, str(msg_len).encode() + msg)
        return msg

    except ConnectionResetError:
        return None
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
        clients[tid] = Client(tid, "guest", "guest", 0, 0, None, False)   # Setting client state
        if (code == b"RSAR"):
            shared_secret = rsa_exchange(sock, tid)
        if (shared_secret == ""):
            return

        clients[tid].shared_secret = shared_secret
        clients[tid].encryption = True
    except Exception:
        print(traceback.format_exc())
        # Releasing clienk and closing socket
        print(f'Client {tid} connection error')
        if (tid in clients):
            clients[tid].user = "dead"
        sock.close()
        return
    while not finish:   # Main client loop
        if all_to_die:
            print('will close due to main server issue')
            break
        try:
            # Recieving data and  handling client
            entire_data = recv_data(sock, tid)
            to_send, finish = handle_request(entire_data, tid, sock)
            if to_send != None:
                send_data(sock, tid, to_send)
            if finish or to_send == None:
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
    try:
        create_keys()
        load_keys()
    except:
        srv_sock.close()

    print('Main thread: before accepting ...\n')
    while True:
        cli_sock, addr = srv_sock.accept()
        t = threading.Thread(target=handle_client, args=(
            cli_sock, str(i), addr))   # Accepting client and assigning id
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
