# 2024 © Idan Hazay
# Import libraries

import traceback, time, os
from modules import validity
from modules.config import *
from modules.limits import Limits
from modules.errors import Errors
from filelock import FileLock

class Protocol:
    def __init__(self, network, clients, cr, files_uploading):
        self.network = network
        self.clients = clients
        self.v = validity.Validation()
        self.cr = cr
        self.files_uploading = files_uploading
        self.files_in_use = []
    
    def protocol_build_reply(self, request, tid, sock):
        """
        Client request parsing and handling
        Getting the input fields
        Checking the action code
        Performing actions for each different code
        Returning the reply to the client
        """
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
            self.clients[tid].id = tid
            self.clients[tid].user = "dead"

        elif (code == "LOGN"):   # Client requests login
            cred = fields[1]
            password = fields[2]
            if (self.v.is_empty(fields[1:])):
                return Errors.EMPTY_FIELD.value
            elif (self.v.check_illegal_chars(fields[1:])):
                return Errors.INVALID_CHARS.value

            if (self.cr.login_validation(cred, password)):
                if (not self.cr.verified(cred)):
                    reply = Errors.NOT_VERIFIED.value

                else:
                    user_dict = self.cr.get_user_data(cred)
                    username = user_dict["username"]
                    email = user_dict["email"]
                    self.clients[tid].id = user_dict["id"]
                    self.clients[tid].user = user_dict["username"]
                    self.clients[tid].email = user_dict["email"]
                    self.clients[tid].cwd = f""
                    self.clients[tid].subscription_level = user_dict["subscription_level"]
                    self.clients[tid].admin_level = user_dict["admin_level"]
                    reply = f"LOGS|{email}|{username}|{int(self.clients[tid].subscription_level)}"
            else:
                reply = Errors.LOGIN_DETAILS.value

        elif (code == "SIGU"):   # Client requests signup
            email = fields[1]
            username = fields[2]
            password = fields[3]
            confirm_password = fields[4]

            if (self.v.is_empty(fields[1:])):
                return Errors.EMPTY_FIELD.value
            elif (self.v.check_illegal_chars(fields[1:])):
                return Errors.INVALID_CHARS.value
            elif (not self.v.is_valid_email(email)):
                return Errors.INVALID_EMAIL.value
            elif (not self.v.is_valid_username(username) or username == "guest"):
                return Errors.INVALID_USERNAME.value
            elif (not self.v.is_valid_password(password)):
                return Errors.PASSWORD_REQ.value
            elif (password != confirm_password):
                return Errors.PASSWORDS_MATCH.value

            if (self.cr.user_exists(username)):
                reply = Errors.USER_REGISTERED.value
            elif (self.cr.email_registered(email)):
                reply = Errors.EMAIL_REGISTERED.value
            else:
                user_details = [email, username, password]
                self.cr.signup_user(user_details)
                self.cr.send_verification(email)
                reply = f"SIGS|{email}|{username}|{password}"

        elif (code == "FOPS"):   # Client requests password reset code
            email = fields[1]
            if (self.v.is_empty(fields[1:])):
                return Errors.EMPTY_FIELD.value
            elif (self.v.check_illegal_chars(fields[1:])):
                return Errors.INVALID_CHARS.value
            elif (not self.v.is_valid_email(email)):
                return Errors.INVALID_EMAIL.value

            if (self.cr.email_registered(email)):
                if (not self.cr.verified(email)):
                    reply = Errors.NOT_VERIFIED.value
                else:
                    self.cr.send_reset_mail(email)
                    reply = f"FOPR|{email}"
            else:
                reply = Errors.EMAIL_NOT_REGISTERED.value

        elif (code == "PASR"):   # Client requests password reset
            email = fields[1]
            code = fields[2]
            new_password = fields[3]
            confirm_new_password = fields[4]

            if (self.v.is_empty(fields[1:])):
                return Errors.EMPTY_FIELD.value
            elif (self.v.check_illegal_chars(fields[1:])):
                return Errors.INVALID_CHARS.value
            elif (not self.v.is_valid_password(new_password)):
                return Errors.PASSWORD_REQ.value
            elif (new_password != confirm_new_password):
                return Errors.PASSWORDS_MATCH.value

            res = self.cr.check_code(email, code)
            if (res == "ok"):
                self.cr.change_password(email, new_password)
                self.clients[tid].user = "guest"
                reply = f"PASS|{email}|{new_password}"
            elif (res == "code"):
                reply = Errors.NOT_MATCHING_CODE.value
            else:
                reply = Errors.CODE_EXPIRED.value

        elif (code == "LOGU"):   # Client requests logout
            self.clients[tid].id = tid
            self.clients[tid].user = "guest"
            self.clients[tid].email = "guest"
            self.clients[tid].cwd = f""
            self.clients[tid].subscription_level = 0
            self.clients[tid].admin_level = 0
            reply = "LUGR"

        elif (code == "SVER"):   # Client requests account verification code
            email = fields[1]

            if (self.v.is_empty(fields[1:])):
                return Errors.EMPTY_FIELD.value
            elif (self.v.check_illegal_chars(fields[1:])):
                return Errors.INVALID_CHARS.value
            elif (not self.v.is_valid_email(email)):
                return Errors.INVALID_EMAIL.value

            if (self.cr.email_registered(email)):
                if (self.cr.verified(email)):
                    reply = Errors.ALREADY_VERIFIED.value
                else:
                    self.cr.send_verification(email)
                    reply = f"VERS|{email}"
            else:
                reply = Errors.EMAIL_NOT_REGISTERED.value

        elif (code == "VERC"):   # Client requests account verification
            email = fields[1]
            code = fields[2]

            if (self.v.is_empty(fields[1:])):
                return Errors.EMPTY_FIELD.value
            elif (self.v.check_illegal_chars(fields[1:])):
                return Errors.INVALID_CHARS.value
            elif (not self.v.is_valid_email(email)):
                return Errors.INVALID_EMAIL.value

            if (self.cr.email_registered(email)):
                res = self.cr.check_code(email, code)
                if (res == "ok"):
                    self.cr.verify_user(email)
                    self.cr.send_welcome_mail(email)
                    reply = f"VERR|{email}"
                elif (res == "code"):
                    reply = Errors.NOT_MATCHING_CODE.value
                else:
                    reply = Errors.CODE_EXPIRED.value
            else:
                reply = Errors.EMAIL_NOT_REGISTERED.value

        elif (code == "DELU"):   # Client requests user deletion
            email = fields[1]
            id = self.clients[tid].id
            if (self.cr.user_exists(id)):
                self.cr.delete_user(id)
                self.clients[tid].id = tid
                self.clients[tid].user = "guest"
                reply = f"DELR|{email}"
            else:
                reply = Errors.LOGIN_DETAILS.value

        elif (code == "FILS" or code == "UPFL"):
            file_name = fields[1]
            parent = fields[2]
            size = int(fields[3])
            id = fields[4]
            try:
                if (self.is_guest(tid)):
                    reply = Errors.NOT_LOGGED.value
                elif (not self.cr.is_dir_owner(self.clients[tid].id, parent)):
                    reply = Errors.NO_PERMS.value
                elif (size > Limits(self.clients[tid].subscription_level).max_file_size * 1_000_000):
                    reply = Errors.SIZE_LIMIT.value + " " + str(Limits(self.clients[tid].subscription_level).max_file_size) + " MB"
                elif (self.cr.get_user_storage(self.clients[tid].user) > Limits(self.clients[tid].subscription_level).max_storage * 1_000_000):
                    reply = Errors.MAX_STORAGE.value
                elif (id in self.files_uploading.keys()):
                    reply = Errors.ALREADY_UPLOADING.value
                else:
                    if code == "UPFL":
                        name = self.cr.get_file_sname(file_name)
                        if os.path.exists(CLOUD_PATH + "\\" + name):
                            os.remove(CLOUD_PATH + "\\" + name)
                        self.files_uploading[id] = File(name, parent, size, id, file_name)
                        self.cr.update_file_size(file_name, size)
                        reply = f"UPFR|{file_name}|was updated succefully"
                    else:
                        name = self.cr.gen_file_name()
                        self.files_uploading[id] = File(name, parent, size, id, file_name)
                        #self.cr.new_file(name, file_name, parent, self.clients[tid].id, size)
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
                if id in self.files_uploading.keys():
                    file = self.files_uploading[id]
                    break
                time.sleep(1)
            if file == None: return Errors.FILE_NOT_FOUND.value + "|" + id
            
            if (self.is_guest(tid)):
                reply = Errors.NOT_LOGGED.value
            elif (not self.cr.is_dir_owner(self.clients[tid].id, file.parent)):
                reply = Errors.NO_PERMS.value
            elif (file.size > Limits(self.clients[tid].subscription_level).max_file_size * 1_000_000):
                reply = Errors.SIZE_LIMIT.value + " " + str(Limits(self.clients[tid].subscription_level).max_file_size) + " MB"
            elif (self.cr.get_user_storage(self.clients[tid].user) > Limits(self.clients[tid].subscription_level).max_storage * 1_000_000):
                reply = Errors.MAX_STORAGE.value
            else:
                if location_infile + len(data) > file.size:
                    return Errors.FILE_SIZE.value
                file.add_data(data, location_infile)
                if code == "FILE":
                    if file.name != self.clients[tid].user:
                        self.cr.new_file(file.name, file.file_name, file.parent, self.clients[tid].id, file.size)
                        reply = f"FILR|{file.file_name}|File finished uploading"
                    else: reply = f"ICUP|Profile icon uploaded"
                    if id in self.files_uploading.keys():
                        del self.files_uploading[id]
                else: reply = ""
        

        elif (code == "GETP" or code == "GETD" or code == "GESP" or code == "GESD" or code == "GEDP" or code == "GEDD"):
            directory = fields[1]
            amount = int(fields[2])
            sort = fields[3]
            sort_direction = fields[4] == "True"
            if (len(fields) == 6): search_filter = fields[5]
            else: search_filter = None
            if (self.v.check_illegal_chars(fields[1:])):
                return Errors.INVALID_CHARS.value
            prev_amount = 0
            if (code == "GETP"):
                items = self.cr.get_files(self.clients[tid].id, directory, search_filter)
                reply = "PATH"
            elif (code == "GETD"):
                items = self.cr.get_directories(self.clients[tid].id, directory, search_filter)
                prev_amount = len(self.cr.get_files(self.clients[tid].id, directory, search_filter))
                reply = "PATD"
            elif (code == "GESP"):
                items = self.cr.get_share_files(self.clients[tid].id, directory, search_filter)
                reply = "PASH"
            elif (code == "GESD"):
                items = self.cr.get_share_directories(self.clients[tid].id, directory, search_filter)
                prev_amount = len(self.cr.get_share_files(self.clients[tid].id, directory, search_filter))
                reply = "PASD"
            elif (code == "GEDP"):
                items = self.cr.get_deleted_files(self.clients[tid].id, directory, search_filter)
                reply = "PADH"
            elif (code == "GEDD"):
                items = self.cr.get_deleted_directories(self.clients[tid].id, directory, search_filter)
                prev_amount = len(self.cr.get_deleted_files(self.clients[tid].id, directory, search_filter))
                reply = "PADD"
            
            total = len(items) + prev_amount
            amount-=prev_amount
            if amount > len(items): amount = len(items)
            elif amount < 0: amount = 0
            
            if sort == "Name" or ((code == "GETD" or code == "GESD" or code == "GEDD") and sort) == "Owner":
                items = sorted(items, key=lambda x: x.split("~")[0].lower(), reverse=sort_direction)
                
            elif sort == "Date":
                if (code == "GETD" or code == "GESD" or code == "GEDD"): 
                    items = sorted(items, key=lambda x: self.cr.str_to_date(x.split("~")[2]), reverse=sort_direction)
                else:
                    items = sorted(items, key=lambda x: self.cr.str_to_date(x.split("~")[1]), reverse=sort_direction)

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
            if (self.cr.valid_directory(directory_id, self.clients[tid].id) or directory_id == ""):
                self.clients[tid].cwd = directory_id
                reply = f"MOVR|{directory_id}|{self.cr.get_parent_directory(directory_id)}|{self.cr.get_full_path(directory_id)}|moved succesfully"
                
            else:
                self.clients[tid].cwd = ""
                reply = f"MOVR|{""}|{self.cr.get_parent_directory("")}|{self.cr.get_full_path("")}|moved succesfully"

        elif (code == "DOWN"):
            file_id = fields[1]
            if "~" in file_id:
                name = fields[2]
                ids = file_id.split("~")
                for id in ids:
                    if(not self.cr.can_download(self.clients[tid].id, id) or self.is_guest(tid)):
                        reply = Errors.NO_PERMS.value
                        return reply
                    elif (self.cr.get_file_sname(id) == None and self.cr.get_dir_name(id) == None):
                        reply = Errors.FILE_NOT_FOUND.value + "|" + file_id
                        return reply
                zip_buffer = self.cr.zip_files(ids)
                self.send_zip(zip_buffer, file_id, sock, tid)
                zip_buffer.close()
                reply = f"DOWR|{name}|{file_id}|was downloaded"
            else:
                if(not self.cr.can_download(self.clients[tid].id, file_id) or self.is_guest(tid)):
                    reply = Errors.NO_PERMS.value
                    return reply
                elif (self.cr.get_dir_name(file_id) != None):
                    zip_buffer = self.cr.zip_directory(file_id)
                    self.send_zip(zip_buffer, file_id, sock, tid)
                    zip_buffer.close()
                    reply = f"DOWR|{self.cr.get_dir_name(file_id)}|{file_id}|was downloaded"
                    return reply
                elif(self.cr.get_file_sname(file_id) == None):
                    reply = Errors.FILE_NOT_FOUND.value + "|" + file_id
                    return reply
                file_path = CLOUD_PATH + "\\" + self.cr.get_file_sname(file_id)
                if (self.cr.get_file_sname(file_id) == None or not os.path.isfile(file_path)):
                    reply = Errors.FILE_NOT_FOUND.value + "|" + file_id
                else:
                    try:
                        self.send_file_data(file_path, file_id, sock, tid)
                        reply = f"DOWR|{self.cr.get_file_fname(file_id)}|was downloaded"
                    except Exception:
                        reply = Errors.FILE_DOWNLOAD.value

        elif (code == "NEWF"):
            folder_name = fields[1]
            folder_path = self.clients[tid].cwd
            if not self.cr.is_dir_owner(self.clients[tid].id, folder_path) or self.is_guest(tid):
                reply = Errors.NO_PERMS.value
            else:
                self.cr.create_folder(folder_name, folder_path, self.clients[tid].id)
                reply = f"NEFR|{folder_name}|was created"

        elif (code == "RENA"):
            file_id = fields[1]
            name = fields[2]
            new_name = fields[3]

            if (self.v.is_empty(fields[1:])):
                return Errors.EMPTY_FIELD.value
            elif(not self.cr.can_rename(self.clients[tid].id, file_id)):
                reply = Errors.NO_PERMS.value
            else:
                if (self.cr.get_file_fname(file_id) is not None):
                    self.cr.rename_file(file_id, new_name)
                else:
                    self.cr.rename_directory(file_id, new_name)
                reply = f"RENR|{name}|{new_name}|File renamed succefully"

        elif (code == "GICO"):
            if (os.path.isfile(os.path.join(USER_ICONS_PATH, self.clients[tid].id) + ".ico")):
                self.send_file_data(os.path.join(USER_ICONS_PATH, self.clients[tid].id) + ".ico", "user", sock, tid)
            else:
                self.send_file_data(os.path.join(USER_ICONS_PATH, "guest.ico"), "user", sock, tid)
            reply = f"GICR|Sent use profile picture"

        elif (code == "ICOS"):
            size = int(fields[3])
            id = fields[4]
            try:
                self.files_uploading[id] = File(self.clients[tid].id, "", size, id, self.clients[tid].id, icon=True)
                reply = f"ICOR|Profile icon started uploading"

            except Exception:
                print(traceback.format_exc())
                reply = Errors.FILE_UPLOAD.value

        elif code == 'DELF':
            file_id = fields[1]
            if(not self.cr.can_delete(self.clients[tid].id, file_id)):
                reply = Errors.NO_PERMS.value
            elif file_id in self.files_in_use:
                reply = Errors.IN_USE.value
            elif self.cr.get_file_fname(file_id) is not None:
                name = self.cr.get_file_fname(file_id)
                self.cr.delete_file(file_id)
                reply = f"DLFR|{name}|was deleted!"
            elif self.cr.get_dir_name(file_id) is not None:
                name = self.cr.get_dir_name(file_id)
                self.cr.delete_directory(file_id)
                reply = f"DFFR|{name}|was deleted!"
            else:
                reply = Errors.FILE_NOT_FOUND.value + "|" + file_id
            

        elif code == "SUBL":
            level = fields[1]
            if (level == self.clients[tid].subscription_level):
                reply = Errors.SAME_LEVEL.value
            elif (int(level) < 0 or int(level) > 3):
                reply = Errors.INVALID_LEVEL.value
            else:
                self.cr.change_level(self.clients[tid].id, int(level))
                self.clients[tid].subscription_level = int(level)
                reply = f"SUBR|{level}|Subscription level updated"

        elif code == "GEUS":
            used_storage = self.cr.get_user_storage(self.clients[tid].id)
            reply = f"GEUR|{used_storage}"

        elif code == "CHUN":
            new_username = fields[1]
            if (self.v.is_empty(fields[1:])):
                return Errors.EMPTY_FIELD.value
            elif (self.v.check_illegal_chars(fields[1:])):
                return Errors.INVALID_CHARS.value
            elif (not self.v.is_valid_username(new_username) or new_username == "guest"):
                return Errors.INVALID_USERNAME.value
            elif (self.cr.user_exists(new_username)):
                reply = Errors.USER_REGISTERED.value
            else:
                self.cr.change_username(self.clients[tid].id, new_username)
                self.clients[tid].user = new_username
                reply = f"CHUR|{new_username}|Changed username"
        
        elif code == "VIEW":
            file_id = fields[1]
            file_path = CLOUD_PATH + "\\" + self.cr.get_file_sname(file_id)
            if(not self.cr.can_download(self.clients[tid].id, file_id)):
                reply = Errors.NO_PERMS.value + "|" + self.cr.get_file_fname(file_id)
            elif (not os.path.isfile(file_path)):
                reply = Errors.FILE_NOT_FOUND.value + "|" + file_id
            elif (os.path.getsize(file_path) > 10_000_000):
                reply = f"{Errors.PREVIEW_SIZE.value}|{self.cr.get_file_fname(file_id)}"
            elif file_id in self.files_in_use:
                reply = Errors.IN_USE.value
            else:
                try:
                    self.send_file_data(file_path, file_id, sock, tid)
                    self.files_in_use.append(file_id)
                    reply = f"VIER|{self.cr.get_file_fname(file_id)}|was viewed"
                except Exception:
                    reply = Errors.FILE_DOWNLOAD.value


        elif code == "GENC":
            if (self.is_guest(tid)):
                reply = Errors.NOT_LOGGED.value
            else:
                self.cr.generate_cookie(self.clients[tid].id)
                reply = f"COOK|{self.cr.get_cookie(self.clients[tid].id)}"
        
        elif code == "COKE":
            cookie = fields[1]
            user_dict = self.cr.get_user_data(cookie)
            if user_dict is None:
                reply = Errors.INVALID_COOKIE.value
            elif self.cr.cookie_expired(user_dict["id"]):
                reply = Errors.EXPIRED_COOKIE.value
            else:
                username = user_dict["username"]
                email = user_dict["email"]
                self.clients[tid].id = user_dict["id"]
                self.clients[tid].user = user_dict["username"]
                self.clients[tid].email = user_dict["email"]
                self.clients[tid].cwd = f""
                self.clients[tid].subscription_level = user_dict["subscription_level"]
                self.clients[tid].admin_level = user_dict["admin_level"]
                reply = f"LOGS|{email}|{username}|{int(self.clients[tid].subscription_level)}"
        
        elif code == "SHRS":
            file_id = fields[1]
            user_cred = fields[2]
            if self.cr.get_file_fname(file_id) is None and self.cr.get_dir_name(file_id) is None:
                reply = Errors.FILE_NOT_FOUND.value + "|" + file_id
            elif(not self.cr.can_share(self.clients[tid].id, file_id)):
                reply = Errors.NO_PERMS.value
            elif user_cred == self.clients[tid].email or user_cred == self.clients[tid].user:
                reply = Errors.SELF_SHARE.value
            elif (self.cr.is_file_owner(self.cr.get_user_id(user_cred), file_id) or self.cr.is_dir_owner(self.cr.get_user_id(user_cred), file_id)):
                reply = Errors.OWNER_SHARE.value
            elif(self.cr.get_user_data(user_cred) is None):
                reply = Errors.USER_NOT_FOUND.value
            else:
                sharing = self.cr.get_share_options(file_id, user_cred)
                if sharing is None:
                    reply = f"SHRR|{file_id}|{user_cred}|{self.cr.get_file_fname(file_id)}"
                else:
                    reply = f"SHRR|{file_id}|{user_cred}|{self.cr.get_file_fname(file_id)}|" + "|".join(sharing[4:])
        
        elif code == "SHRP":
            file_id = fields[1]
            user_cred = fields[2]
            if self.cr.get_file_fname(file_id) is None and self.cr.get_dir_name(file_id) is None:
                reply = Errors.FILE_NOT_FOUND.value + "|" + file_id
            elif(not self.cr.can_share(self.clients[tid].id, file_id)):
                reply = Errors.NO_PERMS.value
            elif user_cred == self.clients[tid].email or user_cred == self.clients[tid].user:
                reply = Errors.SELF_SHARE.value
            elif (self.cr.is_file_owner(self.cr.get_user_id(user_cred), file_id) or self.cr.is_dir_owner(self.cr.get_user_id(user_cred), file_id)):
                reply = Errors.OWNER_SHARE.value
            elif(self.cr.get_user_data(user_cred) is None):
                reply = Errors.USER_NOT_FOUND.value
            else:
                self.cr.share_file(file_id, user_cred, fields[3:])
                reply = f"SHPR|Sharing option with {user_cred} have been updated"
        elif code == "SHRE":
            id = fields[1]
            file_name = self.cr.get_file_fname(id)
            dir_name = self.cr.get_dir_name(id)
            if file_name is None and dir_name is None:
                reply = Errors.FILE_NOT_FOUND.value + "|" + id
            self.cr.remove_share(self.clients[tid].id, id)
            if file_name != None: name = file_name
            else: name = dir_name
            reply = f"SHRM|{name}|Share removed"
                
        
        elif code == "RECO":
            id = fields[1]
            if(not self.cr.can_delete(self.clients[tid].id, id)):
                reply = Errors.NO_PERMS.value
            elif self.cr.get_file_fname(id) is not None:
                name = self.cr.get_file_fname(id)
            elif self.cr.get_dir_name(id) is not None:
                name = self.cr.get_dir_name(id)
            if name is None:
                reply = Errors.FILE_NOT_FOUND.value + "|" + id
            else:
                self.cr.recover(id)
                reply = f"RECR|{name}|was recovered!"
        elif code == "VIEE":
            file_id = fields[1]
            self.files_in_use.remove(file_id)
            reply = f"VIRR|{file_id}|stop viewing"
        elif code == "STOP":
            id = fields[1]
            name = self.remove_file_mid_down(id)
            reply = f"STOR|{name}|{id}|File upload stopped"
        elif code == "RESU":
            id = fields[1]
            if id in self.files_uploading.keys():
                progress = self.files_uploading[id].curr_location_infile
                reply = f"RESR|{id}|{progress}"
            else: reply = Errors.FILE_NOT_FOUND.value + "|" + id
        elif code == "RESD":
            id = fields[1]
            progress = int(fields[2])
            if self.cr.get_file_sname(id) != None: 
                file_path = CLOUD_PATH + "\\" + self.cr.get_file_sname(id)
                self.send_file_data(file_path, id, sock, tid, progress)
            elif self.cr.get_dir_name(id) != None: 
                zip_buffer = self.cr.zip_directory(id)
                self.send_zip(zip_buffer, id, sock, tid)
                zip_buffer.close()
            elif "~" in id:
                ids = id.split("~")
                zip_buffer = self.cr.zip_files(ids)
                self.send_zip(zip_buffer, id, sock, tid)
                zip_buffer.close()
            else:
                reply = Errors.FILE_NOT_FOUND.value + "|" + id
                return reply
            
            reply = f"RUSR|{id}|{progress}"
        elif code == "UPDT":
            msg = fields[1]
            reply = f"UPDR|{msg}"
        else:
            reply = Errors.UNKNOWN.value
            fields = ''
        return reply
    
    def send_file_data(self, file_path, id, sock, tid, progress = 0):
        lock_path = f"{file_path}.lock"
        lock = FileLock(lock_path)

        if not os.path.isfile(file_path):
            raise Exception
        size = os.path.getsize(file_path)
        left = size % CHUNK_SIZE
        sent = progress
        
        start = time.time()
        bytes_sent = 0
        try:
            with lock:
                with open(file_path, 'rb') as f:
                    f.seek(progress)
                    for i in range((size - progress) // CHUNK_SIZE):
                        location_infile = f.tell()
                        data = f.read(CHUNK_SIZE)
                        current_time = time.time()
                        elapsed_time = current_time - start
                        
                        if elapsed_time >= 1.0:
                            start = current_time
                            bytes_sent = 0
                        
                        self.network.send_data(sock, tid, f"RILD|{id}|{location_infile}|".encode() + data)
                        bytes_sent += len(data)
                        sent += CHUNK_SIZE
                        
                        if bytes_sent >= (Limits(self.clients[tid].subscription_level).max_download_speed) * 1_000_000:
                            time_to_wait = 1.0 - elapsed_time
                            if time_to_wait > 0:
                                time.sleep(time_to_wait)
                        
                    location_infile = f.tell()
                    data = f.read(left)
                    if data != b"":
                        self.network.send_data(sock, tid, f"RILE|{id}|{location_infile}|".encode() + data)
        except:
            print(traceback.format_exc())
            if os.path.exists(lock_path):
                os.remove(lock_path)
            raise



    def send_zip(self, zip_buffer, id, sock, tid, progress = 0):
        size = len(zip_buffer.getbuffer())
        left = size % CHUNK_SIZE
        sent = progress
        start = time.time()
        bytes_sent = 0
        try:
            zip_buffer.seek(progress)
            for i in range((size - progress) // CHUNK_SIZE):
                location_infile = zip_buffer.tell()
                data = zip_buffer.read(CHUNK_SIZE)
                
                current_time = time.time()
                elapsed_time = current_time - start
                        
                if elapsed_time >= 1.0:
                    start = current_time
                    bytes_sent = 0
                
                self.networksend_data(sock, tid, f"RILD|{id}|{location_infile}|".encode() + data)
                bytes_sent += len(data)
                sent += CHUNK_SIZE 
                if bytes_sent >= (Limits(self.clients[tid].subscription_level).max_download_speed) * 1_000_000:
                    time_to_wait = 1.0 - elapsed_time
                    if time_to_wait > 0:
                        time.sleep(time_to_wait)
            location_infile = zip_buffer.tell()
            data = zip_buffer.read(left)
            if data != b"":
                self.network.send_data(sock, tid, f"RILE|{id}|{location_infile}|".encode() + data)
        except:
            raise
    
    def is_guest(self, tid):
        return self.clients[tid].user == "guest"
    
    def remove_file_mid_down(self, id):
        if id in self.files_uploading.keys():
            name = self.files_uploading[id].file_name
            file_id = self.cr.get_file_id(self.files_uploading[id].name)
            self.cr.delete_file(file_id)
            self.cr.delete_file(file_id)
            del self.files_uploading[id]
            return name
        
class File:
    def __init__(self, name, parent, size, id, file_name, curr_location_infile = 0, icon = False):
        self.name = name
        self.parent = parent
        self.uploading = True
        self.size = size
        self.id = id
        self.file_name = file_name
        self.curr_location_infile = curr_location_infile
        if icon: self.save_path = USER_ICONS_PATH + "\\" + self.name + ".ico"
        else: self.save_path = CLOUD_PATH + "\\" + self.name
        
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
    
    