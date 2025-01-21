from modules.config import * 
from modules.file_sending import File
from modules import helper, key_exchange
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileDialog, QApplication
import time, socket

class Protocol():
    def __init__(self, network, window, ip = "127.0.0.1", port = 31026):
        self.network = network
        self.window = window
        self.ip = ip
        self.port = port
    
    
    def change_share(self):
        share = not share
        self.move_dir("")

    def change_deleted(self):
        deleted = not deleted
        self.move_dir("")
    
    def view_file(self, file_id, file_name, size):
        self.send_data(b"VIEW|" + file_id.encode())
        save_path = f"{os.getcwd()}\\temp-{file_name}"
        self.window.files_downloading[file_id] = File(self.window, save_path, file_id, size, True, file_name=file_name)
    
    def get_file_progress(self):
        uploading_files = self.window.json.get_files_uploading_data()
        if uploading_files == None: return
        for file_id, details in uploading_files.items():
            self.send_data(f"RESU|{file_id}".encode())
    
    def request_resume_download(self):
        uploading_files = self.window.json.get_files_downloading_data()
        # Iterate through the dictionary and print file_id and file_path
        if uploading_files == None: return
        for file_id, details in uploading_files.items():
            file_path = details.get("file_path")
            if not os.path.exists(file_path): continue
            progress = details.get("progress")
            self.send_data(f"RESD|{file_id}|{progress}".encode())
            self.window.files_downloading[file_id] = File(self.window, file_path, file_id, details.get("size"), file_name=details.get("file_name"))
    
    
    def send_cookie(self):
        try:
            with open(cookie_path, "r") as f:
                cookie = f.read()
                self.send_data(b"COKE|" + cookie.encode())
        except:
            print(traceback.format_exc())
            pass
    
    def get_cwd_files(self, filter=None):
        self.get_files(1, filter)

    def get_cwd_shared_files(self, filter=None):
        self.get_files(2, filter)

    def get_deleted_files(self, filter=None):
        self.get_files(3, filter)

    def get_cwd_directories(self, filter=None):
        self.get_files(4, filter)

    def get_cwd_shared_directories(self, filter=None):
        self.get_files(5, filter)

    def get_deleted_directories(self, filter=None):
        self.get_files(6, filter)
        
    def get_files(self, type, filter):
        get_types = {1: ["GETP", "PATH"], 2: ["GESP", "PASH"], 3: ["GEDP", "PADH"], 4: ["GETD", "PATD"], 5: ["GESD", "PASD"], 6: ["GEDD", "PADD"]}
        to_send = f"{get_types[type][0]}|{self.window.user["cwd"]}|{self.window.current_files_amount}|{self.window.sort}|{self.window.sort_direction}".encode()
        if filter:
            to_send += b"|" + filter.encode()
        self.send_data(to_send)

    def send_share_premissions(self, dialog, file_id, user_cred, read, write, delete, rename, download, share):
        dialog.accept()
        to_send = f"SHRP|{file_id}|{user_cred}|{read}|{write}|{delete}|{rename}|{download}|{share}"
        self.send_data(to_send.encode())

    def change_username(self):
        name = self.window.user["username"]
        new_name = self.window.new_name_dialog("Change Username", "Enter new  username:", name)
        if new_name is not None and new_name != name:
            self.send_data(b"CHUN|" + new_name.encode())


    def subscribe(self, level):
        self.send_data(b"SUBL|" + str(level).encode())

    def move_dir(self, new_dir):
        self.send_data(f"MOVD|{new_dir}".encode())


    def get_user_icon(self):
        self.send_data(b"GICO")
        self.window.files_downloading["user"] = File(self.window, user_icon, "user", 0, file_name="User Icon")


    def get_used_storage(self):
        self.send_data(b"GEUS")

    def login(self, cred, password, remember_temp):
        """
        Send login request to server
        """
        self.window.remember = remember_temp
        items = [cred, password]
        send_string = helper.build_req_string("LOGN", items)
        self.send_data(send_string)
        


    def logout(self):
        """
        Send logout request to server
        """
        send_string = helper.build_req_string("LOGU")
        self.send_data(send_string)


    def signup(self, email, username, password, confirm_password):
        """
        Send signup request to server
        """
        items = [email, username, password, confirm_password]

        send_string = helper.build_req_string("SIGU", items)
        self.send_data(send_string)


    def reset_password(self, email):
        """
        Send password reset request to server
        """
        items = [email]
        send_string = helper.build_req_string("FOPS", items)
        self.send_data(send_string)


    def password_recovery(self, email, code, new_password, confirm_new_password):
        """
        Send password recovery code and new password to server
        """
        items = [email, code, new_password, confirm_new_password]
        send_string = helper.build_req_string("PASR", items)
        self.send_data(send_string)


    def send_verification(self, email):
        """
        Send verification request to server
        """
        items = [email]
        send_string = helper.build_req_string("SVER", items)
        self.send_data(send_string)


    def verify(self, email, code):
        """
        Send verification code to server for confirmation
        """
        items = [email, code]
        send_string = helper.build_req_string("VERC", items)
        self.send_data(send_string)



    def delete_user(self, email):
        """
        Send delete user request to server
        """
        if (self.window.confirm_account_deletion(email)):
            items = [email]
            send_string = helper.build_req_string("DELU", items)
            self.send_data(send_string)
    
    def view_file(self, file_id, file_name, size):
        self.send_data(b"VIEW|" + file_id.encode())
        save_path = f"{os.getcwd()}\\temp-{file_name}"
        self.window.files_downloading[file_id] =File(self.window, save_path, file_id, size, True, file_name=file_name)

    
    def end_view(self, file_id):
        self.send_data(b"VIEE|" + file_id.encode())
        
    def update_userpage(self, msg):
        self.send_data(f"UPDT|{msg}".encode())
    
    def exit_program(self):
        """
        Send exit request to server
        """
        send_string = helper.build_req_string("EXIT")
        self.send_data(send_string)
    
    def upload_icon(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self.window, "Open File", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.ico);")
            if file_path:
                self.window.file_sending.file_queue.extend([file_path])
                self.send_files("ICOS")
        except:
            print(traceback.format_exc())
    
    def download(self):
        if len(self.window.currently_selected) == 1:
            btn = self.window.currently_selected[0]
            file_name = btn.text().split(" | ")[0][1:]
            if btn.is_folder: 
                file_path, _ = QFileDialog.getSaveFileName(btn, "Save File", file_name, "Zip Files (*.zip);;All Files (*)")
            else: 
                file_path, _ = QFileDialog.getSaveFileName(btn, "Save File", file_name, "Text Files (*.txt);;All Files (*)")
            if file_path:
                self.send_data(b"DOWN|" + btn.id.encode())
                self.window.files_downloading[btn.id] = File(self.window, file_path, btn.id, btn.file_size, file_name=file_name)
                self.window.json.update_json(False, btn.id, file_path,file=self.window.files_downloading[btn.id], progress=0)
                try: self.window.file_upload_progress.show()
                except: pass
        else:
            file_path, _ = QFileDialog.getSaveFileName(self.window, "Save File", "", "Zip Files (*.zip);;All Files (*)")
            name = file_path.split("/")[-1]
            ids = "~".join(btn.id for btn in self.window.currently_selected)
            size = sum(btn.file_size for btn in self.window.currently_selected)
            if file_path:
                self.send_data(f"DOWN|{ids}|{name}".encode())
                self.window.files_downloading[ids] = File(self.window, file_path, ids, size, file_name=name)
                self.window.json.update_json(False, ids, file_path, file=self.window.files_downloading[ids], progress=0)
                try: self.window.file_upload_progress.show()
                except: pass


    def delete(self):
        if self.window.show_confirmation_dialog(f"Are you sure you want to delete {len(self.window.currently_selected)} files?"):
            for btn in self.window.currently_selected:
                self.send_data(b"DELF|" + btn.id.encode())
            self.window.protocol.update_userpage(f"Succesfully deleted {len(self.window.currently_selected)} files")
            self.window.currently_selected = []

    def share_action(self):
        user_email = self.window.new_name_dialog("Share", f"Enter email/username of the user you want to share {len(self.window.currently_selected)} files with:")
        if user_email is not None:
            for btn in self.window.currently_selected:
                self.send_data(b"SHRS|" + btn.id.encode() + b"|" + user_email.encode())
            self.window.protocol.update_userpage(f"Succesfully shared {len(self.window.currently_selected)} files")
        
    def remove(self):
        for btn in currently_selected:
            self.send_data(B"SHRE|" + btn.id.encode())
        self.window.protocol.update_userpage(f"Succesfully removed {len(currently_selected)} files from share")
        currently_selected = []
        
    def recover(self):
        for btn in currently_selected:
            self.send_data(b"RECO|" + btn.id.encode())  
        self.window.protocol.update_userpage(f"Succesfully recovered {len(currently_selected)} files")
        currently_selected = []


    def new_folder(self):
        new_folder = helper.new_name_dialog("New Folder", "Enter new folder name:")
        if new_folder is not None:
            self.send_data(b"NEWF|" + new_folder.encode())


    def search(self):
        search_filter = self.window.new_name_dialog("Search", "Enter search filter:", search_filter)
        self.window.user_page()
    
    def protocol_parse_reply(self, reply):
        """
        Server reply parsing and handeling
        Checking error codes and respective answers to user
        Performing action according to response from server
        """
        try:
            to_show = 'Invalid reply from server'
            if reply == None:
                return None
            # Parse the reply and aplit it according to the protocol seperator
            fields = reply.split(b"|")
            code = fields[0].decode()
        
            if code != "RILD" and code != "RILE":
                fields = reply.decode().split("|")
            
            if code == 'ERRR':   # If server returned error show to user the error
                err_code = int(fields[1])
                self.window.set_error_message(fields[2])
                if (err_code == 9):
                    self.window.send_verification_page()
                elif (err_code == 14):
                    try:
                        file_id = fields[3]
                        self.window.json.update_json(True, file_id, "", remove=True)
                    except: 
                        print(traceback.format_exc())
                elif (err_code == 20):
                    if self.window.file_sending.active_threads != []:
                        self.window.file_sending.active_threads[0].running = False
                elif (err_code == 22 or err_code == 26):
                    try:
                        name = fields[3]
                        file_path = f"{os.getcwd()}\\temp-{name}"
                        if os.path.exists(file_path): os.remove(file_path)
                    except: pass
                    

                to_show = 'Server return an error: ' + fields[1] + ' ' + fields[2]

            # Handle each response accordingly
            elif code == 'EXTR':   # Server exit success
                to_show = 'Server acknowledged the exit message'

            elif code == 'LOGS':   # Login succeeded
                email = fields[1]
                username = fields[2]
                to_show = f'Login was succesfull for user: {username}'
                search_filter = None
                self.window.user["email"] = email
                self.window.user["username"] = username
                self.window.user["subscription_level"] = fields[3]
                self.get_user_icon()
                if self.window.user["username"].lower() == "emily":
                    with open(f"{os.getcwd()}/gui/css/emily.css", 'r') as f: self.app.setStyleSheet(f.read())
                self.window.user_page()
                self.window.set_message("Login was succesfull!")
                if self.window.remember:
                    self.send_data(b"GENC")

            elif code == 'SIGS':   # Signup was performed
                email = fields[1]
                username = fields[2]
                password = fields[3]
                to_show = f'Signup was successful for user: {username}, password:{password}'

                self.window.verification_page(email)
                self.window.set_message(f"Signup for user {username} completed. Verification code was sent to your email please verify your account")

            elif code == 'FOPR':   # Recovery mail sent
                to_show = f'Password reset code was sent to {fields[1]}'
                self.window.recovery(fields[1])
                self.window.set_message(to_show)

            elif code == 'PASS':   # Password was reset
                new_pwd = fields[2]
                to_show = f'Password was reset for user: {fields[1]}, new password: {new_pwd}'
                self.logout()
                self.window.main_page()
                self.window.set_message("Password reset successful, please sign in again with your new password")

            elif code == 'LUGR':   # Logout was performed
                if self.window.user["username"].lower() == "emily":
                    with open(f"{os.getcwd()}/gui/css/style.css", 'r') as f: self.app.setStyleSheet(f.read())
                self.window.user["email"] = "guest"
                self.window.user["username"] = "guest"
                self.window.user["subscription_level"] = 0
                self.window.user["cwd"] = ""
                self.window.user["parent_cwd"] = ""
                self.window.user["cwd_name"] = ""
                share = False
                deleted = False
                to_show = f'Logout succesfull'
                self.window.main_page()
                self.window.set_message(to_show)

            elif code == 'VERS':   # Account verification mail sent
                email = fields[1]
                to_show = f'Verification sent to email {email}'
                self.window.verification_page(email)
                self.window.set_message(f'Verification email was sent to {email}')

            elif code == 'VERR':   # Verification succeeded
                username = fields[1]
                to_show = f'Verification for user {username} was succesfull'

                self.window.main_page()
                self.window.set_message(f"Verification for user {username} completed. You may now log in to your account")

            elif code == 'DELR':   # User deletion succeeded
                username = fields[1]
                to_show = f'User {username} was deleted'
                self.window.main_page()
                self.window.set_message(to_show)

            elif code == 'FILR':
                to_show = f'File {fields[1]} was uploaded'
                if time.time() - last_load > 0.5:
                    self.window.user_page()
                    last_load = time.time()
                self.window.set_message(to_show)
            
            elif code == 'FISS':
                to_show = f'File {fields[1]} started uploading'
                self.window.set_message(to_show)

            elif code == 'MOVR':
                self.window.user["cwd"] = fields[1]
                self.window.user["parent_cwd"] = fields[2]
                self.window.user["cwd_name"] = fields[3]
                to_show = f'Succesfully moved to {fields[3]}'
                self.window.scroll_progress = 0
                self.window.current_files_amount = items_to_load
                self.window.user_page()
                
            elif code == "RILD" or code == "RILE":
                file_id = fields[1].decode()
                location_infile = int(fields[2].decode())
                data = reply[4 + len(file_id) + len(str(location_infile)) + 3:]
                if file_id in self.window.files_downloading.keys():
                    file = self.window.files_downloading[file_id]
                    file.add_data(data, location_infile)
                
                if code == "RILE":
                    if file_id in self.window.files_downloading.keys():
                        if self.window.files_downloading[file_id].is_view:
                            self.end_view(file_id)
                            self.window.activate_file_view(file_id)
                        self.window.json.update_json(False, file_id, "", remove=True)
                        self.window.set_message(f"File {self.window.files_downloading[file_id].file_name} finished downloading")
                        del self.window.files_downloading[file_id]
                    try: 
                        self.window.stop_button.setEnabled(False)
                        self.window.stop_button.hide()
                    except: pass
                    try: self.window.file_upload_progress.hide()
                    except: pass
                to_show = "File data recieved " + str(location_infile)
                

            elif code == 'DOWR':
                to_show = f'File {fields[1]} was downloaded'
                self.window.set_message(to_show)

            elif code == 'NEFR':
                to_show = f'Folder {fields[1]} was created'
                self.window.user_page()
                self.window.set_message(to_show)

            elif code == 'RENR':
                to_show = f'File/Folder {fields[1]} was renamed to {fields[2]}'
                self.window.user_page()
                self.window.set_message(to_show)

            elif code == 'GICR':
                to_show = "Profile picture was recieved"
                try:
                    if share or deleted: self.window.upload_button.setIcon((QIcon(user_icon)))
                    self.window.user_button.setIcon((QIcon(user_icon)))
                except: pass
            
            elif code == 'ICOR':
                to_show = "Profile icon started uploading succefully!"
                self.window.set_message(to_show)
            
            elif code == 'ICUP':
                to_show = "Profile icon uploaded succefully!"
                self.get_user_icon()
            elif code == 'DLFR':
                file_name = fields[1]
                to_show = f"File {file_name} was deleted!"
                self.window.set_message(to_show)

            elif code == 'DFFR':
                folder_name = fields[1]
                to_show = f"Folder {folder_name} was deleted!"
                self.window.set_message(to_show)

            elif code == 'SUBR':
                level = fields[1]
                self.window.user["subscription_level"] = level
                sub = "free"
                if level == "1":
                    sub = "basic"
                if level == "2":
                    sub = "premium"
                if level == "3":
                    sub = "professional"
                to_show = f"Subscription level updated to {sub}"
                self.window.subscriptions_page()
                self.window.set_message(to_show)

            elif code == 'GEUR':
                used_storage = round(int(fields[1])/1_000_000, 3)
                self.window.set_used_storage()
                to_show = f"Current used storage is {used_storage}"

            elif code == 'CHUR':
                new_username = fields[1]
                self.window.user["username"] = new_username
                to_show = f"Username changed to {new_username}"
                self.window.manage_account()
                self.window.set_message(to_show)
            elif code == 'VIER':
                file_name = fields[1]
                to_show = f"File {file_name} was viewed"
                self.window.set_message(to_show)
            elif code == 'COOK':
                cookie = fields[1]
                save_cookie(cookie)
                to_show = f"Cookie recieved"
            elif code == "SHRR":
                file_id = fields[1]
                user_cred = fields[2]
                file_name = fields[3]
                if len(fields) == 3:
                    self.window.share_file(file_id, user_cred, file_name)
                else:
                    self.window.share_file(file_id, user_cred, file_name, *fields[4:])
                to_show = "Sharing options recieved"
            elif code == "SHPR":
                to_show = fields[1]
                self.window.set_message(to_show)
            elif code == "SHRM":
                name = fields[1]
                to_show = f"Succefully remove {name} from share"
                self.window.set_message(to_show)
            elif code == "RECR":
                name = fields[1]
                to_show = f"Succefully recovered {name}"
                self.window.set_message(to_show)
            elif code == "UPFR":
                name = fields[1]
                to_show = f"Succefully saved changes to file {name}"
                self.window.user_page()
                self.window.set_message(to_show)
            elif code == "VIRR":
                to_show = "File viewing released"
            elif code == "STOR":
                name = fields[1]
                id = fields[2]
                to_show = f"Upload of {name} stopped"
                if self.window.file_sending.active_threads != []: self.window.file_sending.active_threads[0].running = False
                self.window.json.update_json(True, id, "", remove=True)
                self.window.set_message(to_show)
            elif code == "PATH" or code == "PASH" or code == "PADH":
                self.window.files = fields[2:]
                if self.window.files != None and self.window.directories != None:
                    self.window.update_current_files()
                to_show = "Got files"
            elif code == "PATD" or code == "PASD" or code == "PADD":
                self.window.items_amount = fields[1]
                self.window.total_files.setText(f"{self.window.items_amount} items")
                self.window.directories = fields[2:]
                if self.window.files != None and self.window.directories != None:
                    self.window.update_current_files()
                to_show = "Got directories"
            elif code == "RESR":
                file_id = fields[1]
                progress = fields[2]
                self.window.file_sending.resume_files_upload(file_id, progress)
                to_show = f"File upload of file {file_id} continued at {progress}"
            elif code == "RUSR":
                id = fields[1]
                progress = fields[2]
                to_show = f"Resumed download of file {id} from byte {progress}"
            elif "UPDR":
                msg = fields[1]
                self.window.user_page()
                self.window.set_message(msg)
                to_show = msg
                
            else:
                self.window.set_message("Unknown command " + code)
            if code != "RILD" and code != "RILE": self.window.force_update_window()
                
        except Exception as e:   # Error
            print(traceback.format_exc())
        return to_show
    
    # Main function and start of code
    def connect_server(self, new_ip, new_port, receive_thread, loop = False):
        self.window.set_message(f"Trying to connect to {new_ip} {new_port}...")
        QApplication.processEvents()
        try:
            self.ip = new_ip
            self.port = int(new_port)
            sock = socket.socket()
            self.ip, self.port = self.network.search_server()
            self.port = int(self.port)
            sock.connect((self.ip, self.port))
            self.network.set_sock(sock)
            exchange = key_exchange.KeyExchange(self.network)
            shared_secret = exchange.rsa_exchange() 
            if not shared_secret:
                sock.close()
                return
            self.network.set_secret(shared_secret)
            self.window.main_page()
            receive_thread.start()
            receive_thread.resume()
            self.send_cookie()
            self.get_file_progress()
            self.request_resume_download()
                
            if self.window.user["username"] != "guest":
                self.window.set_message(f'Connect succeeded {self.ip} {self.port}')
            return sock
        except:
            print(traceback.format_exc())
            if not loop:
                receive_thread.pause()
                self.window.not_connected_page()
            self.window.set_error_message(f'Server was not found {self.ip} {self.port}')
            return None
    
    def send_data(self, bdata, encryption = True):
        try: self.network.send_data_wrap(bdata, encryption)
        except ConnectionResetError:
            self.network.sock.close()
            self.window.not_connected_page()
            self.window.set_error_message("Lost connection to server")
        except:
            print(traceback.format_exc())
            
def save_cookie(cookie):
    if not os.path.exists(os.getcwd() + "\\cookies"):
        os.makedirs(os.getcwd() + "\\cookies")
    with open(cookie_path, "w") as f:
        f.write(cookie)