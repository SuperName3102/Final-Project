# 2024 © Idan Hazay
# Import libraries

from modules import encrypting
from modules.dialogs import *
from modules.helper import *

import socket
import sys
import traceback
import rsa
import struct
import os

from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QWidget, QMessageBox, QApplication, QVBoxLayout, QPushButton, QFileDialog, QLineEdit, QGridLayout, QScrollArea, QHBoxLayout, QSpacerItem, QSizePolicy, QMenu, QInputDialog
from PyQt6.QtGui import QIcon, QContextMenuEvent
from PyQt6.QtCore import QSize, Qt


# Announce global vars
len_field = 4    
user = {}
encryption = False
chunk_size = 65536
cwd = ""
user_icon = f"{os.path.dirname(os.path.abspath(__file__))}/assets/user.ico"
log = False


# Begin gui related functions

class FileButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("""
            QPushButton {
                border-radius: 3px;  # Half of the width/height to make it round
                font-size: 13px;
                text-align: center;
                padding: 5px;
            }
        """)

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)
        action = menu.addAction("Download")
        action.triggered.connect(self.download)
        
        action = menu.addAction("Delete")
        action.triggered.connect(self.delete)
        
        action = menu.addAction("Rename")
        action.triggered.connect(self.rename)
                
        action = menu.addAction("Share")
        action.triggered.connect(self.share)
        
        action = menu.addAction("New Folder")
        action.triggered.connect(self.new_folder)
        
        menu.exec(event.globalPos())

    def download(self):
        file_name = self.text().split(" | ")[0]
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", file_name, "Text Files (*.txt);;All Files (*)")
        if file_path:
            send_data(b"DOWN|" + file_name.encode())
            save_file(file_path)
    
    def rename(self):
        name = self.text().split(" | ")[0]
        new_name = new_name_dialog("Rename", "Enter new file name:", name)
        if new_name is not None:
            send_data(b"RENA|" + name.encode() + b"|" + new_name.encode())
            handle_reply()
    
    def delete(self):
        name = self.text().split(" | ")[0]
        if show_confirmation_dialog("Are you sure you want to delete " + name):
            send_data(b"DELF|" + name.encode() + b"|")
            handle_reply()
    
    def share(self):
        print(self.text())
    
    def new_folder(self):
        new_folder = new_name_dialog("New Folder", "Enter new folder name:")
        if new_folder is not None:
            send_data(b"NEWF|" + new_folder.encode())
            handle_reply()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_page()
        if (os.path.isfile(f"{os.path.dirname(os.path.abspath(__file__))}/assets/icon.ico")):
            self.setWindowIcon(QIcon(f"{os.path.dirname(os.path.abspath(__file__))}/assets/icon.ico"))

        self.setFixedSize(1000, 550)
    
    def main_page(self):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/main.ui", self)
            
            self.signup_button.clicked.connect(self.signup_page)
            self.login_button.clicked.connect(self.login_page)
            self.exit_button.clicked.connect(exit_program)

        except:
            print(traceback.format_exc())
        
    def signup_page(self):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/signup.ui", self)
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.signup_button.clicked.connect(lambda: signup(self.email.text(), self.username.text(), self.password.text(), self.confirm_password.text()))
            self.signup_button.setShortcut("Return")
            self.back_button.clicked.connect(self.main_page)
            self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))
            self.confirm_password_toggle.clicked.connect(lambda: self.toggle_password(self.confirm_password))
            self.login_button.clicked.connect(self.login_page)
            self.login_button.setStyleSheet("background-color:transparent;color:royalblue;text-decoration: underline;font-size:14px;border:none;")
        except:
            print(traceback.format_exc())
        

    def login_page(self):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/login.ui", self)
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.login_button.clicked.connect(lambda: login(self.user.text(), self.password.text()))
            self.login_button.setShortcut("Return")
            self.back_button.clicked.connect(self.main_page)
            self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))
            self.forgot_password_button.clicked.connect(self.forgot_password)
            self.forgot_password_button.setStyleSheet("background-color:transparent;color:royalblue;text-decoration: underline;font-size:14px;border:none;")
            
            self.signup_button.clicked.connect(self.signup_page)
            self.signup_button.setStyleSheet("background-color:transparent;color:royalblue;text-decoration: underline;font-size:14px;border:none;")
        except:
            print(traceback.format_exc())
    
    def forgot_password(self):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/forgot_password.ui", self)
            self.send_code_button.clicked.connect(lambda: reset_password(self.email.text()))
            self.send_code_button.setShortcut("Return")
            self.back_button.clicked.connect(self.login_page)
        except:
            print(traceback.format_exc())

    def verification_page(self, email):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/verification.ui", self)
            self.verify_button.clicked.connect(lambda: verify(email, self.code.text()))
            self.verify_button.setShortcut("Return")
            self.send_again_button.clicked.connect(lambda: send_verification(email))
            self.back_button.clicked.connect(self.main_page)
        except:
            print(traceback.format_exc())
        
    
    def send_verification_page(self):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/send_verification.ui", self)
            self.send_code_button.clicked.connect(lambda: send_verification(self.email.text()))
            self.send_code_button.setShortcut("Return")
            self.back_button.clicked.connect(self.main_page)
        except:
            print(traceback.format_exc())
    
    
    def user_page(self):
        try:
            files = get_cwd_files()
            directories = get_cwd_directories()
            
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/user.ui", self)
            
            self.set_cwd()
            self.draw_cwd(files, directories)

            self.main_text.setText(f"Welcome {user["username"]}")
            
            self.user_button.clicked.connect(lambda: self.manage_account())
            self.logout_button.clicked.connect(logout)
            self.upload_button.clicked.connect(lambda: self.file_dialog())
            self.user_button.setFixedSize(50, 50)
            self.user_button.setIconSize(QSize(40, 40))
            self.user_button.setStyleSheet("padding:0px;border-radius:5px;")
            try:
                self.user_button.setIcon((QIcon(user_icon)))
            except:
                pass
        except:
            print(traceback.format_exc())


    def draw_cwd(self, files, directories):
        try:
            central_widget = self.centralWidget()

            outer_layout = QVBoxLayout()
            outer_layout.addStretch(1)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)

            scroll_container_widget = QWidget()
            scroll_layout = QGridLayout()
            scroll_layout.setSpacing(5)
            

            for i, file in enumerate(files):
                file_name = file.split("~")[0]
                size = format_file_size(int(file.split("~")[-1]))
                file = " | ".join(file.split("~")[:-1])
                button = FileButton(f"{file} | {size}")
                button.setStyleSheet("background-color:dimgrey;border:1px solid darkgrey;font-size:14px;border-radius: 3px;")
                button.clicked.connect(lambda checked, b=button: b.download())
                scroll_layout.addWidget(button)

            for index, directory in enumerate(directories):
                button = FileButton(directory)
                button.setStyleSheet("background-color:peru;font-size:14px;border-radius: 3px;border:1px solid peachpuff;")
                button.clicked.connect(lambda checked, d=directory: move_dir(d))
                scroll_layout.addWidget(button)

            if(directories == [] and files == []):
                button = FileButton("No files or folders in this directory")
                button.setStyleSheet("background-color:dimgrey;font-size:14px;border-radius: 3px;border:1px solid darkgrey;")
                scroll_layout.addWidget(button)

            if(cwd != user["username"]):
                button = FileButton("Back")
                button.setStyleSheet("background-color:green;font-size:14px;border-radius: 3px;border:1px solid lightgreen;")
                button.clicked.connect(lambda: move_dir("/.."))
                scroll_layout.addWidget(button)
            
            scroll_container_widget.setLayout(scroll_layout)

            scroll.setWidget(scroll_container_widget)
            scroll.setFixedSize(QSize(900, 340))
            spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            outer_layout.addItem(spacer)

            center_layout = QHBoxLayout()
            center_layout.addStretch(1)  # Add stretchable space on the left
            center_layout.addWidget(scroll)  # Add the scroll area
            center_layout.addStretch(1)  # Add stretchable space on the right

            # Add the centered scroll area layout to the outer layout
            outer_layout.addLayout(center_layout)
            outer_layout.addStretch(1)
            central_widget.setLayout(outer_layout)
        except:
            print(traceback.format_exc())
    
    
    def manage_account(self):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/account_managment.ui", self)
            
            self.forgot_password_button.clicked.connect(lambda: reset_password(user["email"]))
            self.delete_account_button.clicked.connect(lambda: delete_user(user["email"]))
            self.upload_icon_button.clicked.connect(lambda: upload_icon())
            self.back_button.clicked.connect(self.user_page)
        except:
            print(traceback.format_exc())
    
    def recovery(self, email):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/recovery.ui", self)
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
            
            self.back_button.clicked.connect(self.manage_account)
            self.reset_button.clicked.connect(lambda: password_recovery(email, self.code.text(), self.password.text(), self.confirm_password.text()))
            self.reset_button.setShortcut("Return")
            
            self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))
            self.confirm_password_toggle.clicked.connect(lambda: self.toggle_password(self.confirm_password))
            self.send_again_button.clicked.connect(lambda: reset_password(email))
        except:
            print(traceback.format_exc())
    
    def toggle_password(self, text):
        if text.echoMode()==QLineEdit.EchoMode.Normal:
            text.setEchoMode(QLineEdit.EchoMode.Password)
        else:
            text.setEchoMode(QLineEdit.EchoMode.Normal)
    
    
    def file_dialog(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Text Files (*.txt)")

            if file_path:
                file_name = file_path.split("/")[-1]
                size = os.path.getsize(file_path)
                start_string = b'FILS|' + file_path.encode() + b'|' + file_name.encode() + b'|' + str(size).encode()
                send_data(start_string)
                send_file(file_path)
        except:
            print(traceback.format_exc())
    
    def set_error_message(self, msg):
        try:
            if (hasattr(self, "message")):
                self.message.setStyleSheet("color: red; font-size: 15px;")
                self.message.setText(msg)
        except Exception:
            pass
    
    def set_message(self, msg):
        if (hasattr(self, "message")):
            self.message.setStyleSheet("color: lightgreen; font-size: 15px;")
            self.message.setText(msg)
    
    def set_cwd(self):
        if (hasattr(self, "cwd")):
            self.cwd.setStyleSheet("color: yellow; font-size: 17px;")
            self.cwd.setText(f"CWD: {cwd}")



# Files functions
def send_file(file_path):
    if(not os.path.isfile(file_path)):
        window.set_error_message(f"File path was not found")
        return
    size = os.path.getsize(file_path)
    left = size % chunk_size
    try:
        with open(file_path, 'rb') as f:
            for i in range(size//chunk_size):
                data = f.read(chunk_size)
                send_data(b"FILD" + data)
            data = f.read(left)
            if (data != b""):
                send_data(b'FILE' + data)
    except:
        print(traceback.format_exc())
    finally:
        handle_reply()


def save_file(save_loc):
    try:
        if not os.path.exists(os.path.dirname(save_loc)):
            os.makedirs(os.path.dirname(save_loc))
        data = b''
        with open(save_loc, 'wb') as f:
            while True:
                data = recv_data()
                if not data:
                    raise Exception
                if (data[:4] == b"RILD"):
                    f.write(data[4:])
                elif (data[:4] == b"RILE"):
                    f.write(data[4:])
                    break
                else:
                    protocol_parse_reply(data)
                    return
                data = b''
    except:
        print(traceback.format_exc())
    finally:
        handle_reply()

def move_dir(new_dir):
    send_data(f"MOVD|{new_dir}".encode())
    handle_reply()


def get_user_icon():
    send_data(b"GICO")
    save_file(user_icon)

def upload_icon():
    try:
        file_path, _ = QFileDialog.getOpenFileName(window, "Open File", "", "Icon Files (*.ico);")

        if file_path:
            file_name = file_path.split("/")[-1]
            size = os.path.getsize(file_path)
            start_string = b'ICOS|' + file_path.encode() + b'|' + file_name.encode() + b'|' + str(size).encode()
            send_data(start_string)
            send_file(file_path)
    except:
        print(traceback.format_exc())



# Begin server requests related functions


def login(cred, password):
    """
    Send login request to server
    """
    items = [cred, password]
    send_string = build_req_string("LOGN", items)
    send_data(send_string)
    handle_reply()

def logout():
    """
    Send logout request to server
    """
    global logged_in_user
    logged_in_user = {}
    send_string = build_req_string("LOGU")
    send_data(send_string)
    handle_reply()

def signup(email, username, password, confirm_password):
    """
    Send signup request to server
    """
    items = [email, username, password, confirm_password]

    send_string = build_req_string("SIGU", items)
    send_data(send_string)
    handle_reply()

def reset_password(email):
    """
    Send password reset request to server
    """
    items = [email]
    send_string = build_req_string("FOPS", items)
    send_data(send_string)
    handle_reply()

def password_recovery(email, code, new_password, confirm_new_password):
    """
    Send password recovery code and new password to server
    """
    items = [email, code, new_password, confirm_new_password]
    send_string = build_req_string("PASR", items)
    send_data(send_string)
    handle_reply()

def send_verification(email):
    """
    Send verification request to server
    """
    items = [email]
    send_string = build_req_string("SVER", items)
    send_data(send_string)
    handle_reply()

def verify(email, code):
    """
    Send verification code to server for confirmation
    """
    items = [email, code]
    send_string = build_req_string("VERC", items)
    send_data(send_string)
    handle_reply()

def delete_user(email):
    """
    Send delete user request to server
    """
    if(confirm_account_deletion(email)):
        items = [email]
        send_string = build_req_string("DELU", items)
        send_data(send_string)
        handle_reply()

def confirm_account_deletion(email):
    # Create a QApplication instance if needed
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    app.setWindowIcon(QIcon(f"{os.path.dirname(os.path.abspath(__file__))}/assets/icon.ico"))
    while True:
        # Create input dialog asking for email confirmation
        entered_email, ok = QInputDialog.getText(None, "Account delete confirmation", "Enter your email to confirm:")
        if not ok:
            return False
        if entered_email == email:
            return True
        else:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Icon.Warning)
            error_msg.setWindowTitle("Error")
            error_msg.setText("The email you entered does not match account email.")
            error_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            error_msg.exec()

def exit_program():
    """
    Send exit request to server
    """
    send_string = build_req_string("EXIT")
    send_data(send_string)
    handle_reply()


def get_cwd_files():
    send_data(b"GETP")
    data = recv_data()
    try:
        if (data[:4] != b"PATH"):
            return []
        data = data.decode()
        return data.split("|")[1:]
    except Exception:
        print(traceback.format_exc())
        return []

def get_cwd_directories():
    send_data(b"GETD")
    data = recv_data()
    try:
        if (data[:4] != b"PATD"):
            return []
        data = data.decode()
        return data.split("|")[1:]
    except Exception:
        print(traceback.format_exc())
        return []



# Key exchange

def rsa_exchange():
    global encryption
    send_data(b"RSAR")
    recv_rsa_key()
    send_shared_secret()
    encryption = True

def recv_rsa_key():
    """
    RSA key recieve from server
    Gets the length of the key in binary
    Gets the useable key and saves it as global var for future use
    """
    global s_public_key

    key_len_b = b""
    while(len(key_len_b) < len_field):   # Recieve the length of the key
        key_len_b += sock.recv(len_field - len(key_len_b))
    key_len = int(struct.unpack("!l", key_len_b)[0])

    key_binary = b""
    while(len(key_binary) < key_len):   # Recieve the key according to its length
        key_binary += sock.recv(key_len - len(key_binary))
    
    logtcp('recv', key_len_b + key_binary)
    s_public_key = rsa.PublicKey.load_pkcs1(key_binary)   # Save the key

def send_shared_secret():
    """
    Create and send the shared secret
    to server via secure rsa connection
    """
    global shared_secret
    shared_secret = os.urandom(16)
    key_to_send = rsa.encrypt(shared_secret, s_public_key)
    key_len = struct.pack("!l", len(key_to_send))
    to_send = key_len + key_to_send
    sock.send(to_send)


# Begin server replies handling functions

def protocol_parse_reply(reply):
    """
    Server reply parsing and handeling
    Checking error codes and respective answers to user
    Performing action according to response from server
    """
    global cwd
    try:
        to_show = 'Invalid reply from server'
        if reply == None:
            return None
        reply = reply.decode()   # Parse the reply and aplit it according to the protocol seperator
        fields = reply.split("|")
        code = fields[0]
        if code == 'ERRR':   # If server returned error show to user the error
            err_code = int(fields[1])
            window.set_error_message(fields[2])
            if(err_code == 9):
                window.send_verification_page()
            
            to_show = 'Server return an error: ' + fields[1] + ' ' + fields[2]
        

        # Handle each response accordingly
        elif code == 'EXTR':   # Server exit success
            to_show = 'Server acknowledged the exit message'
        
        elif code == 'LOGS':   # Login succeeded
            email = fields[1]
            username = fields[2]
            password = fields[3]
            to_show = f'Login was succesfull for user: {username}, password:{password}'
            user["email"] = email
            user["username"] = username
            user["password"] = password
            get_user_icon()
            cwd = username
            window.user_page()
            window.set_message("Login was succesfull!")
            
        
        elif code == 'SIGS':   # Signup was performed
            email = fields[1]
            username = fields[2]
            password = fields[3]
            to_show = f'Signup was successful for user: {username}, password:{password}'
            
            window.verification_page(email)
            window.set_message(f"Signup for user {username} completed. Verification code was sent to your email please verify your account")
            
        
        elif code == 'FOPR':   # Recovery mail sent
            to_show = f'Password reset code was sent to {fields[1]}'
            window.recovery(fields[1])
            window.set_message(to_show)
        
        elif code == 'PASS':   # Password was reset
            new_pwd = fields[2]
            to_show = f'Password was reset for user: {fields[1]}, new password: {new_pwd}'
            window.main_page()
            window.set_message("Password reset successful, please sign in again with your new password")
        
        elif code == 'LUGR':   # Logout was performed
            to_show = f'Logout succesfull'
            window.main_page()
            window.set_message(to_show)
        
        elif code == 'VERS':   # Account verification mail sent
            email = fields[1]
            to_show = f'Verification sent to email {email}'
            window.verification_page(email)
            window.set_message(f'Verification email was sent to {email}')
        
        elif code == 'VERR':   # Verification succeeded
            username = fields[1]
            to_show = f'Verification for user {username} was succesfull'
            
            window.main_page()
            window.set_message(f"Verification for user {username} completed. You may now log in to your account")
        
        elif code == 'DELR':   # User deletion succeeded
            username = fields[1]
            to_show = f'User {username} was deleted'
            window.main_page()
            window.set_message(to_show)
        
        elif code == 'FILR':
            to_show = f'File {fields[1]} was uploaded'
            
            window.user_page()
            window.set_message(to_show)
        
        elif code == 'MOVR':
            to_show = f'Directory {fields[1]} was moved into'
            cwd = fields[1]
            window.user_page()
        
        elif code == 'DOWR':
            to_show = f'File {fields[1]} was downloaded'
            window.set_message(to_show)
        
        elif code == 'NEFR':
            to_show = f'Folder {fields[1]} was created'
            window.user_page()
            window.set_message(to_show)
        
        elif code == 'RENR':
            to_show = f'File/Folder {fields[1]} was renamed to {fields[2]}'
            window.user_page()
            window.set_message(to_show)
        
        elif code == 'GICR':
            to_show = "Profile picture was recieved"
        
        elif code == 'ICOR':
            to_show = "Profile icon was uploaded succefully!"
            get_user_icon()
            window.set_message(to_show)
        
        elif code == 'DLFR':
            file_name = fields[1]
            to_show = f"File {file_name} was deleted!"
            window.user_page()
            window.set_message(to_show)
        
        elif code == 'DFFR':
            folder_name = fields[1]
            to_show = f"Folder {folder_name} was deleted!"
            window.user_page()
            window.set_message(to_show)
    
    except Exception as e:   # Error
        print('Server replay bad format ' + str(e))
        print(traceback.format_exc())
    return to_show

def handle_reply():
    """
    Getting server reply and parsing it
    If some error occured or no response disconnect
    """
    try:
        reply = recv_data()
        logtcp('recv', reply)

        to_show = protocol_parse_reply(reply)
        if to_show != '':   # If got a reply, show it in console
            print('\n==========================================================')
            print(f'  SERVER Reply: {to_show}')
            print('==========================================================')
        if to_show == "Server acknowledged the exit message" or to_show == None:   # If exit request succeded, dissconnect
            print('Will exit ...')
            sock.close()
            print("Bye...")
            sys.exit(0)
    except socket.error as err:   # General error handling
        print(f'Got socket error: {err}')
        return
    except Exception as err:
        print(f'General error: {err}')
        print(traceback.format_exc())
        return



# Begin data handling and processing functions 

def logtcp(dir, byte_data):
    """
    Loggs the recieved data to console
    """
    if log:
        try:
            if (str(byte_data[0]) == "0"):
                print("")
        except AttributeError:
            return
        if dir == 'sent':   # Sen/recieved labels
            print(f'C LOG:Sent     >>>{byte_data}')
        else:
            print(f'C LOG:Recieved <<<{byte_data}')


def send_data(bdata):
    """
    Send data to server
    Adds data encryption
    Adds length
    Loggs the encrypted and decrtpted data for readablity
    Checks if encryption is used
    """
    if(encryption):
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
    
    try:
        sock.send(to_send)
    except ConnectionResetError:
        pass
        

def recv_data():
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
        
        if(encryption): # If encryption is enabled decrypt and log encrypted
            logtcp('recv', b_len + msg)   # Log encrypted data
            msg = encrypting.decrypt(msg, shared_secret)
            logtcp('recv', bytes(msg_len) + msg)
        
        return msg
    except ConnectionResetError:
        return None
    except Exception as err:
        print(traceback.format_exc())


# Main function and start of code

def main(addr):
    """
    Main function
    Create tkinter root and start secure connection to server
    Connect to server via addr param
    """
    global sock
    global root
    global window
    
    sock = socket.socket()
    try:
        sock.connect(addr)
        print(f'Connect succeeded {addr}')
    except:
        print(
            f'Error while trying to connect.  Check ip or port -- {addr}')
        return
    try:
        rsa_exchange()
        
        # gui = threading.Thread(target=gui.create_root, args=())
        # gui.start()
        #gui.create_root()
        
        app = QtWidgets.QApplication(sys.argv)
        #app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)  # Enable DPI scaling for images
        app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)  # Use high DPI scaling policy
        with open(f"{os.path.dirname(os.path.abspath(__file__))}/gui/css/style.css", 'r') as f:
            app.setStyleSheet(f.read())
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
        
        
    except Exception as e:
        print("Error:" + str(e))
        print(traceback.format_exc())

if __name__ == "__main__":   # Run main
    ip = "127.0.0.1"
    if len(sys.argv) == 2:
        ip = sys.argv[1]
    
    main((ip, 31026))
