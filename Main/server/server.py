# 2024 © Idan Hazay
# Import libraries

from modules import client_requests as cr
from modules import encrypting
from modules import validity as v
from modules.errors import Errors
from modules.limits import Limits, LimitExceeded
from modules.logger import Logger

import socket, traceback, time, threading, os, rsa, struct, sys
from datetime import datetime
from filelock import FileLock
from requests import get

# Announce global vars
all_to_die = False
len_field = 4
sep = "|"
clients = {}
files_in_use = []
chunk_size = 524288
cloud_path = f"{os.path.dirname(os.path.abspath(__file__))}\\cloud"
user_icons_path = f"{os.path.dirname(os.path.abspath(__file__))}\\user icons"
log = False

bytes_recieved = {}
bytes_sent = {}

files_uploading = {}


# User handling classes
class File:
    def __init__(self, name, parent, size, id, file_name, curr_location_infile = 0, icon = False):
        self.name = name
        self.parent = parent
        self.uploading = True
        self.size = size
        self.id = id
        self.file_name = file_name
        self.curr_location_infile = curr_location_infile
        if icon: self.save_path = user_icons_path + "\\" + self.name + ".ico"
        else: self.save_path = cloud_path + "\\" + self.name
        
        self.start_download()
    
    def start_download(self):
        with open(self.save_path, 'wb') as f:
            f.seek(self.size - 1)
            f.write(b"\0")
            f.flush()
    
    def add_data(self, data, location_infile):
        lock_path = f"{self.save_path}.lock"
        lock = FileLock(lock_path)
        try:
            with lock:
                with open(self.save_path, 'r+b') as f:
                    f.seek(location_infile)
                    f.write(data)
                    f.flush()
                    self.curr_location_infile = location_infile
        except:
            print(traceback.format_exc())
            self.uploading = False
        finally:
            try: 
                if os.path.exists(lock_path): os.remove(lock_path)
            except: pass
            
    
    def delete(self):
        lock_path = f"{self.save_path}.lock"
        if os.path.exists(lock_path): os.remove(lock_path)
        if os.path.exists(self.save_path): os.remove(self.save_path)

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


def send_file_data(file_path, id, sock, tid, progress = 0):
    lock_path = f"{file_path}.lock"
    lock = FileLock(lock_path)

    if not os.path.isfile(file_path):
        raise Exception
    size = os.path.getsize(file_path)
    left = size % chunk_size
    sent = progress
    
    start = time.time()
    bytes_sent = 0
    try:
        with lock:
            with open(file_path, 'rb') as f:
                f.seek(progress)
                for i in range((size - progress) // chunk_size):
                    location_infile = f.tell()
                    data = f.read(chunk_size)
                    current_time = time.time()
                    elapsed_time = current_time - start
                    
                    if elapsed_time >= 1.0:
                        start = current_time
                        bytes_sent = 0
                    
                    send_data(sock, tid, f"RILD|{id}|{location_infile}|".encode() + data)
                    bytes_sent += len(data)
                    sent += chunk_size
                    
                    if bytes_sent >= (Limits(clients[tid].subscription_level).max_download_speed) * 1_000_000:
                        time_to_wait = 1.0 - elapsed_time
                        if time_to_wait > 0:
                            time.sleep(time_to_wait)
                    
                location_infile = f.tell()
                data = f.read(left)
                if data != b"":
                    send_data(sock, tid, f"RILE|{id}|{location_infile}|".encode() + data)
    except:
        if os.path.exists(lock_path):
            os.remove(lock_path)
        raise



def send_zip(zip_buffer, id, sock, tid, progress = 0):
    size = len(zip_buffer.getbuffer())
    left = size % chunk_size
    sent = progress
    start = time.time()
    bytes_sent = 0
    try:
        zip_buffer.seek(progress)
        for i in range((size - progress) // chunk_size):
            location_infile = zip_buffer.tell()
            data = zip_buffer.read(chunk_size)
            
            current_time = time.time()
            elapsed_time = current_time - start
                    
            if elapsed_time >= 1.0:
                start = current_time
                bytes_sent = 0
            
            send_data(sock, tid, f"RILD|{id}|{location_infile}|".encode() + data)
            bytes_sent += len(data)
            sent += chunk_size 
            if bytes_sent >= (Limits(clients[tid].subscription_level).max_download_speed) * 1_000_000:
                time_to_wait = 1.0 - elapsed_time
                if time_to_wait > 0:
                    time.sleep(time_to_wait)
        location_infile = zip_buffer.tell()
        data = zip_buffer.read(left)
        if data != b"":
            send_data(sock, tid, f"RILE|{id}|{location_infile}|".encode() + data)
    except:
        raise
    

def is_guest(tid):
    return clients[tid].user == "guest"

def str_to_date(str):
    """
    Transfer string of date to date
    Helper function
    """
    if str == "": return datetime.min
    format = "%Y-%m-%d %H:%M:%S.%f"
    return datetime.strptime(str, format)

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
    global clients, files_in_use
    if request is None:
        return None
    # Parse the reply and aplit it according to the protocol seperator
    fields = request
    fields = fields.split(b"|")
    code = fields[0].decode()
    
    if code != "FILD" and code != "FILE":
        fields = request.decode().split("|")

    # Checking each indevidual code
    if code == 'EXIT':   # Client requests disconnection
        reply = 'EXTR'
        clients[tid].id = tid
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
                clients[tid].id = user_dict["id"]
                clients[tid].user = user_dict["username"]
                clients[tid].email = user_dict["email"]
                clients[tid].cwd = f""
                clients[tid].subscription_level = user_dict["subscription_level"]
                clients[tid].admin_level = user_dict["admin_level"]
                reply = f"LOGS|{email}|{username}|{int(clients[tid].subscription_level)}"
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
        clients[tid].id = tid
        clients[tid].user = "guest"
        clients[tid].email = "guest"
        clients[tid].cwd = f""
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
        id = clients[tid].id
        if (cr.user_exists(id)):
            cr.delete_user(id)
            clients[tid].id = tid
            clients[tid].user = "guest"
            reply = f"DELR|{email}"
        else:
            reply = Errors.LOGIN_DETAILS.value

    elif (code == "FILS" or code == "UPFL"):
        file_name = fields[1]
        parent = fields[2]
        size = int(fields[3])
        id = fields[4]
        try:
            if (is_guest(tid)):
                reply = Errors.NOT_LOGGED.value
            elif (not cr.is_dir_owner(clients[tid].id, parent)):
                reply = Errors.NO_PERMS.value
            elif (size > Limits(clients[tid].subscription_level).max_file_size * 1_000_000):
                reply = Errors.SIZE_LIMIT.value + " " + str(Limits(clients[tid].subscription_level).max_file_size) + " MB"
            elif (cr.get_user_storage(clients[tid].user) > Limits(clients[tid].subscription_level).max_storage * 1_000_000):
                reply = Errors.MAX_STORAGE.value
            elif (id in files_uploading.keys()):
                reply = Errors.ALREADY_UPLOADING.value
            else:
                if code == "UPFL":
                    name = cr.get_file_sname(file_name)
                    if os.path.exists(cloud_path + "\\" + name):
                        os.remove(cloud_path + "\\" + name)
                    files_uploading[id] = File(name, parent, size, id, file_name)
                    cr.update_file_size(file_name, size)
                    reply = f"UPFR|{file_name}|was updated succefully"
                else:
                    name = cr.gen_file_name()
                    files_uploading[id] = File(name, parent, size, id, file_name)
                    #cr.new_file(name, file_name, parent, clients[tid].id, size)
                    reply = f"FISS|{file_name}|Upload started"
        except Exception:
            print(traceback.format_exc())
            reply = Errors.FILE_UPLOAD.value
    
    elif (code == "FILD" or code == "FILE"):
        id = fields[1].decode()
        location_infile = int(fields[2].decode())
        data = request[4 + len(id) + len(str(location_infile)) + 3:]
        
        file = None
        for i in range (5):
            if id in files_uploading.keys():
                file = files_uploading[id]
                break
            time.sleep(1)
        if file == None: return Errors.FILE_NOT_FOUND.value
        
        if (is_guest(tid)):
            reply = Errors.NOT_LOGGED.value
        elif (not cr.is_dir_owner(clients[tid].id, file.parent)):
            reply = Errors.NO_PERMS.value
        elif (file.size > Limits(clients[tid].subscription_level).max_file_size * 1_000_000):
            reply = Errors.SIZE_LIMIT.value + " " + str(Limits(clients[tid].subscription_level).max_file_size) + " MB"
        elif (cr.get_user_storage(clients[tid].user) > Limits(clients[tid].subscription_level).max_storage * 1_000_000):
            reply = Errors.MAX_STORAGE.value
        else:
            if location_infile + len(data) > file.size:
                return Errors.FILE_SIZE.value
            file.add_data(data, location_infile)
            if code == "FILE":
                if file.name != clients[tid].user:
                    cr.new_file(file.name, file.file_name, file.parent, clients[tid].id, file.size)
                    reply = f"FILR|{file.file_name}|File finished uploading"
                else: reply = f"ICUP|Profile icon uploaded"
                if id in files_uploading.keys():
                    del files_uploading[id]
            else: reply = ""
    

    elif (code == "GETP" or code == "GETD" or code == "GESP" or code == "GESD" or code == "GEDP" or code == "GEDD"):
        directory = fields[1]
        amount = int(fields[2])
        sort = fields[3]
        sort_direction = fields[4] == "True"
        if (len(fields) == 6): search_filter = fields[5]
        else: search_filter = None
        if (v.check_illegal_chars(fields[1:])):
            return f"ERRR|102|Invalid chars used"
        prev_amount = 0
        if (code == "GETP"):
            items = cr.get_files(clients[tid].id, directory, search_filter)
            reply = "PATH"
        elif (code == "GETD"):
            items = cr.get_directories(clients[tid].id, directory, search_filter)
            prev_amount = len(cr.get_files(clients[tid].id, directory, search_filter))
            reply = "PATD"
        elif (code == "GESP"):
            items = cr.get_share_files(clients[tid].id, directory, search_filter)
            reply = "PASH"
        elif (code == "GESD"):
            items = cr.get_share_directories(clients[tid].id, directory, search_filter)
            prev_amount = len(cr.get_share_files(clients[tid].id, directory, search_filter))
            reply = "PASD"
        elif (code == "GEDP"):
            items = cr.get_deleted_files(clients[tid].id, directory, search_filter)
            reply = "PADH"
        elif (code == "GEDD"):
            items = cr.get_deleted_directories(clients[tid].id, directory, search_filter)
            prev_amount = len(cr.get_deleted_files(clients[tid].id, directory, search_filter))
            reply = "PADD"
        
        total = len(items) + prev_amount
        amount-=prev_amount
        if amount > len(items): amount = len(items)
        elif amount < 0: amount = 0
        
        if sort == "Name" or ((code == "GETD" or code == "GESD" or code == "GEDD") and sort) == "Owner":
            items = sorted(items, key=lambda x: x.split("~")[0].lower(), reverse=sort_direction)
            
        elif sort == "Date":
            if (code == "GETD" or code == "GESD" or code == "GEDD"): 
                items = sorted(items, key=lambda x: str_to_date(x.split("~")[2]), reverse=sort_direction)
            else:
                items = sorted(items, key=lambda x: str_to_date(x.split("~")[1]), reverse=sort_direction)

        elif sort == "Type" and (code == "GETP" or code == "GESP" or code == "GEDP"):
            items = sorted(items, key=lambda x: x.split("~")[0].split(".")[-1].lower(), reverse=sort_direction)
            
        elif sort == "Size":
            if (code == "GETD" or code == "GESD" or code == "GEDD"): 
                items = sorted(items, key=lambda x: int(x.split("~")[3]), reverse=sort_direction)
            else: 
                items = sorted(items, key=lambda x: int(x.split("~")[2]), reverse=sort_direction)
        elif sort == "Owner" and (code == "GETD" or code == "GESD" or code == "GEDD"):
            items = sorted(items, key=lambda x: x.split("~")[4].lower(), reverse=sort_direction)

        reply += f"|{total}"
        for item in items[:amount]:
            reply += f"|{item}"

    elif (code == "MOVD"):
        directory_id = fields[1]
        if (cr.valid_directory(directory_id, clients[tid].id) or directory_id == ""):
            clients[tid].cwd = directory_id
            reply = f"MOVR|{directory_id}|{cr.get_parent_directory(directory_id)}|{cr.get_full_path(directory_id)}|moved succesfully"
            
        else:
            clients[tid].cwd = ""
            reply = f"MOVR|{""}|{cr.get_parent_directory("")}|{cr.get_full_path("")}|moved succesfully"

    elif (code == "DOWN"):
        file_id = fields[1]
        if "~" in file_id:
            name = fields[2]
            ids = file_id.split("~")
            for id in ids:
                if(not cr.can_download(clients[tid].id, id) or is_guest(tid)):
                    reply = Errors.NO_PERMS.value
                    return reply
                elif (cr.get_file_sname(id) == None and cr.get_dir_name(id) == None):
                    reply = Errors.FILE_NOT_FOUND.value
                    return reply
            zip_buffer = cr.zip_files(ids)
            send_zip(zip_buffer, file_id, sock, tid)
            zip_buffer.close()
            reply = f"DOWR|{name}|{file_id}|was downloaded"
        else:
            if(not cr.can_download(clients[tid].id, file_id) or is_guest(tid)):
                reply = Errors.NO_PERMS.value
                return reply
            elif (cr.get_dir_name(file_id) != None):
                zip_buffer = cr.zip_directory(file_id)
                send_zip(zip_buffer, file_id, sock, tid)
                zip_buffer.close()
                reply = f"DOWR|{cr.get_dir_name(file_id)}|{file_id}|was downloaded"
                return reply
            elif(cr.get_file_sname(file_id) == None):
                reply = Errors.FILE_NOT_FOUND.value
                return reply
            file_path = cloud_path + "\\" + cr.get_file_sname(file_id)
            if (cr.get_file_sname(file_id) == None or not os.path.isfile(file_path)):
                reply = Errors.FILE_NOT_FOUND.value
            else:
                try:
                    send_file_data(file_path, file_id, sock, tid)
                    reply = f"DOWR|{cr.get_file_fname(file_id)}|was downloaded"
                except Exception:
                    reply = Errors.FILE_DOWNLOAD.value

    elif (code == "NEWF"):
        folder_name = fields[1]
        folder_path = clients[tid].cwd
        if not cr.is_dir_owner(clients[tid].id, folder_path) or is_guest(tid):
            reply = Errors.NO_PERMS.value
        else:
            cr.create_folder(folder_name, folder_path, clients[tid].id)
            reply = f"NEFR|{folder_name}|was created"

    elif (code == "RENA"):
        file_id = fields[1]
        name = fields[2]
        new_name = fields[3]

        if (v.is_empty(fields[1:])):
            return f"ERRR|101|Cannot have an empty field"
        elif(not cr.can_rename(clients[tid].id, file_id)):
            reply = Errors.NO_PERMS.value
        else:
            if (cr.get_file_fname(file_id) is not None):
                cr.rename_file(file_id, new_name)
            else:
                cr.rename_directory(file_id, new_name)
            reply = f"RENR|{name}|{new_name}|File renamed succefully"

    elif (code == "GICO"):
        if (os.path.isfile(os.path.join(user_icons_path, clients[tid].id) + ".ico")):
            send_file_data(os.path.join(user_icons_path, clients[tid].id) + ".ico", "user", sock, tid)
        else:
            send_file_data(os.path.join(user_icons_path, "guest.ico"), "user", sock, tid)
        reply = f"GICR|Sent use profile picture"

    elif (code == "ICOS"):
        size = int(fields[3])
        id = fields[4]
        try:
            files_uploading[id] = File(clients[tid].id, "", size, id, clients[tid].id, icon=True)
            reply = f"ICOR|Profile icon started uploading"

        except Exception:
            print(traceback.format_exc())
            reply = Errors.FILE_UPLOAD.value

    elif code == 'DELF':
        file_id = fields[1]
        if(not cr.can_delete(clients[tid].id, file_id)):
            reply = Errors.NO_PERMS.value
        elif file_id in files_in_use:
            reply = Errors.IN_USE.value
        elif cr.get_file_fname(file_id) is not None:
            name = cr.get_file_fname(file_id)
            cr.delete_file(file_id)
            reply = f"DLFR|{name}|was deleted!"
        elif cr.get_dir_name(file_id) is not None:
            name = cr.get_dir_name(file_id)
            cr.delete_directory(file_id)
            reply = f"DFFR|{name}|was deleted!"
        else:
            reply = Errors.FILE_NOT_FOUND.value
        

    elif code == "SUBL":
        level = fields[1]
        if (level == clients[tid].subscription_level):
            reply = Errors.SAME_LEVEL.value
        elif (int(level) < 0 or int(level) > 3):
            reply = Errors.INVALID_LEVEL.value
        else:
            cr.change_level(clients[tid].id, int(level))
            clients[tid].subscription_level = int(level)
            reply = f"SUBR|{level}|Subscription level updated"

    elif code == "GEUS":
        used_storage = cr.get_user_storage(clients[tid].id)
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
            cr.change_username(clients[tid].id, new_username)
            clients[tid].user = new_username
            reply = f"CHUR|{new_username}|Changed username"
    
    elif code == "VIEW":
        file_id = fields[1]
        file_path = cloud_path + "\\" + cr.get_file_sname(file_id)
        if(not cr.can_download(clients[tid].id, file_id)):
            reply = Errors.NO_PERMS.value + "|" + cr.get_file_fname(file_id)
        elif (not os.path.isfile(file_path)):
            reply = Errors.FILE_NOT_FOUND.value
        elif (os.path.getsize(file_path) > 10_000_000):
            reply = f"{Errors.PREVIEW_SIZE.value}|{cr.get_file_fname(file_id)}"
        elif file_id in files_in_use:
            reply = Errors.IN_USE.value
        else:
            try:
                send_file_data(file_path, file_id, sock, tid)
                files_in_use.append(file_id)
                reply = f"VIER|{cr.get_file_fname(file_id)}|was viewed"
            except Exception:
                reply = Errors.FILE_DOWNLOAD.value


    elif code == "GENC":
        if (is_guest(tid)):
            reply = Errors.NOT_LOGGED.value
        else:
            cr.generate_cookie(clients[tid].id)
            reply = f"COOK|{cr.get_cookie(clients[tid].id)}"
    
    elif code == "COKE":
        cookie = fields[1]
        user_dict = cr.get_user_data(cookie)
        if user_dict is None:
            reply = Errors.INVALID_COOKIE.value
        elif cr.cookie_expired(user_dict["id"]):
            reply = Errors.EXPIRED_COOKIE.value
        else:
            username = user_dict["username"]
            email = user_dict["email"]
            clients[tid].id = user_dict["id"]
            clients[tid].user = user_dict["username"]
            clients[tid].email = user_dict["email"]
            clients[tid].cwd = f""
            clients[tid].subscription_level = user_dict["subscription_level"]
            clients[tid].admin_level = user_dict["admin_level"]
            reply = f"LOGS|{email}|{username}|{int(clients[tid].subscription_level)}"
    
    elif code == "SHRS":
        file_id = fields[1]
        user_cred = fields[2]
        if cr.get_file_fname(file_id) is None and cr.get_dir_name(file_id) is None:
            reply = Errors.FILE_NOT_FOUND.value
        elif(not cr.can_share(clients[tid].id, file_id)):
            reply = Errors.NO_PERMS.value
        elif user_cred == clients[tid].email or user_cred == clients[tid].user:
            reply = Errors.SELF_SHARE.value
        elif (cr.is_file_owner(cr.get_user_id(user_cred), file_id) or cr.is_dir_owner(cr.get_user_id(user_cred), file_id)):
            reply = Errors.OWNER_SHARE.value
        elif(cr.get_user_data(user_cred) is None):
            reply = Errors.USER_NOT_FOUND.value
        else:
            sharing = cr.get_share_options(file_id, user_cred)
            if sharing is None:
                reply = f"SHRR|{file_id}|{user_cred}|{cr.get_file_fname(file_id)}"
            else:
                reply = f"SHRR|{file_id}|{user_cred}|{cr.get_file_fname(file_id)}|" + "|".join(sharing[4:])
    
    elif code == "SHRP":
        file_id = fields[1]
        user_cred = fields[2]
        if cr.get_file_fname(file_id) is None and cr.get_dir_name(file_id) is None:
            reply = Errors.FILE_NOT_FOUND.value
        elif(not cr.can_share(clients[tid].id, file_id)):
            reply = Errors.NO_PERMS.value
        elif user_cred == clients[tid].email or user_cred == clients[tid].user:
            reply = Errors.SELF_SHARE.value
        elif (cr.is_file_owner(cr.get_user_id(user_cred), file_id) or cr.is_dir_owner(cr.get_user_id(user_cred), file_id)):
            reply = Errors.OWNER_SHARE.value
        elif(cr.get_user_data(user_cred) is None):
            reply = Errors.USER_NOT_FOUND.value
        else:
            cr.share_file(file_id, user_cred, fields[3:])
            reply = f"SHPR|Sharing option with {user_cred} have been updated"
    elif code == "SHRE":
        id = fields[1]
        file_name = cr.get_file_fname(id)
        dir_name = cr.get_dir_name(id)
        if file_name is None and dir_name is None:
            reply = Errors.FILE_NOT_FOUND.value
        cr.remove_share(clients[tid].id, id)
        if file_name != None: name = file_name
        else: name = dir_name
        reply = f"SHRM|{name}|Share removed"
            
    
    elif code == "RECO":
        id = fields[1]
        if(not cr.can_delete(clients[tid].id, id)):
            reply = Errors.NO_PERMS.value
        elif cr.get_file_fname(id) is not None:
            name = cr.get_file_fname(id)
        elif cr.get_dir_name(id) is not None:
            name = cr.get_dir_name(id)
        if name is None:
            reply = Errors.FILE_NOT_FOUND.value
        else:
            cr.recover(id)
            reply = f"RECR|{name}|was recovered!"
    elif code == "VIEE":
        file_id = fields[1]
        files_in_use.remove(file_id)
        reply = f"VIRR|{file_id}|stop viewing"
    elif code == "STOP":
        id = fields[1]
        name = remove_file_mid_down(id)
        reply = f"STOR|{name}|{id}|File upload stopped"
    elif code == "RESU":
        id = fields[1]
        if id in files_uploading.keys():
            progress = files_uploading[id].curr_location_infile
            reply = f"RESR|{id}|{progress}"
        else: reply = Errors.FILE_NOT_FOUND.value + "|" + id
    elif code == "RESD":
        id = fields[1]
        progress = int(fields[2])
        if cr.get_file_sname(id) != None: 
            file_path = cloud_path + "\\" + cr.get_file_sname(id)
            send_file_data(file_path, id, sock, tid, progress)
        elif cr.get_dir_name(id) != None: 
            zip_buffer = cr.zip_directory(id)
            send_zip(zip_buffer, id, sock, tid)
            zip_buffer.close()
        elif "~" in id:
            ids = id.split("~")
            zip_buffer = cr.zip_files(ids)
            send_zip(zip_buffer, id, sock, tid)
            zip_buffer.close()
        else:
            reply = Errors.FILE_NOT_FOUND.value
            return reply
        
        reply = f"RUSR|{id}|{progress}"
    elif code == "UPDT":
        msg = fields[1]
        reply = f"UPDR|{msg}"
    else:
        reply = Errors.UNKNOWN.value
        fields = ''
    return reply

def remove_file_mid_down(id):
    if id in files_uploading.keys():
        name = files_uploading[id].file_name
        file_id = cr.get_file_id(files_uploading[id].name)
        cr.delete_file(file_id)
        cr.delete_file(file_id)
        del files_uploading[id]
        return name
    

def handle_request(request, tid, sock):
    """
    Getting client request and parsing it
    If some error occured or no response return general error
    """
    global finish
    try:
        to_send = protocol_build_reply(request, tid, sock)
        if to_send == None:
            clients[tid] = None
            print(f"Client {tid} disconnected")
            return
        to_send = to_send.encode()
        send_data(sock, tid, to_send)
        if (to_send == b"EXTR"):
            clients[tid] = None
            print(f"Client {tid} disconnected")

    except Exception as err:
        print(traceback.format_exc())
        to_send = Errors.GENERAL.value
        send_data(sock, tid, to_send.encode())


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
    global bytes_sent
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
        bytes_sent[tid] += len(to_send)
        sock.send(to_send)
    except ConnectionResetError:
        pass


def recv_data(sock, tid):
    """
    Data recieve function
    Gets length of response and then the response
    Makes sure its gotten everything
    """
    global bytes_recieved
    try:
        b_len = b''
        while (len(b_len) < len_field):   # Loop to get length in bytes
            b_len += sock.recv(len_field - len(b_len))
        bytes_recieved[tid] += len(b_len)
        msg_len = struct.unpack("!l", b_len)[0]
        if msg_len == b'':
            print('Seems client disconnected')
        msg = b''

        while (len(msg) < msg_len):   # Loop to recieve the rest of the response
            chunk = sock.recv(msg_len - len(msg))
            bytes_recieved[tid] += len(chunk)
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
    global all_to_die, clients, bytes_sent, bytes_recieved
    try:
        finish = False
        print(f'New Client number {tid} from {addr}')
        bytes_sent[tid] = 0
        bytes_recieved[tid] = 0
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
            clients[tid] = None
        sock.close()
        return
    while not finish and clients[tid] != None:   # Main client loop
        if all_to_die:
            print('will close due to main server issue')
            break
        try:
            # Recieving data and  handling client
            entire_data = recv_data(sock, tid)
            t = threading.Thread(target=handle_request, args=(entire_data, tid, sock))
            t.start()
            
        except socket.error as err:
            print(f'Socket Error exit client loop: err:  {err}')
            break
        except Exception as err:
            print(f'General Error %s exit client loop: {err}')
            print(traceback.format_exc())
            break
    print(f'Client {tid} Exit')   # Releasing clienk and closing socket
    clients[tid] = None
    sock.close()

def cleaner():
    while True:
        cr.clean_db(files_uploading)
        time.sleep(100)

def dhcp_listen():
    dhcp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dhcp_socket.bind(("", 31026))
    while True:
        data, addr = dhcp_socket.recvfrom(1024)
        if data.decode() == "SEAR":
            response_message = f"SERR|{local_ip}|{port}"
            dhcp_socket.sendto(response_message.encode(), addr)

def main(addr):
    """
    Main function
    Listens for clients from any addr
    Creates threads to handle each user
    Handles every user seperately
    """
    global all_to_die, local_ip

    threads = []
    srv_sock = socket.socket()
    srv_sock.bind(addr)
    srv_sock.listen(20)

    print(f"Server listening on {addr}")
    
    try:
        public_ip = get('https://api.ipify.org').content.decode('utf8')
    except Exception:
        public_ip = "No IP found"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Connect to a public DNS server (Google's in this case)
            local_ip = s.getsockname()[0]
    except:
        local_ip = "127.0.0.1"
    
    print(f"Public server ip: {public_ip}, local server ip: {local_ip}")

    srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    i = 1
    try:
        create_keys()
        load_keys()
        scheduler = threading.Thread(target=cleaner)
        scheduler.start()
    except:
        srv_sock.close()

    dhcp_listener = threading.Thread(target=dhcp_listen)
    dhcp_listener.start()
    
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
    sys.stdout = Logger()
    port = 3102
    if len(sys.argv) == 2:
        port = sys.argv[1]
    main(("0.0.0.0", int(port)))
