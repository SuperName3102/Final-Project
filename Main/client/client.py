# 2024 © Idan Hazay
# Import libraries

from modules import encrypting

import socket
import sys
import traceback
from tkinter.messagebox import askyesno
from tkinter import messagebox
import rsa
import struct
import os

from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLineEdit, QGridLayout
from PyQt6.QtGui import QIcon


# Announce global vars
len_field = 4    
sep = "|"
user = {}
encryption = False
chunk_size = 65536
errors = 12

error_messages = {
    1: "General error|uknown",
    2: "something|something",
    3: "somthing|somrthing",
    4: "Invalid Login|Login details not matching any user, please try again",
    5: "Username already registered|Username already registered, please try a different one",
    6: "Email address already registered|Email address already registered, please try a different one",
    7: "Email address not registered|Email address not registered",
    8: "Invalid Code|Code is not matching",
    9: "Code time has expired|Code time has exipred, please send again",
    10: "Account is not verified|Account is not verified, please verify",
    11: "Account is already verified|Account is already verified",
    12: "File upload error|File didnt upload correctly, please try again"
}

# Begin gui related functions
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_page()
        self.setWindowIcon(QIcon(f"{os.path.dirname(os.path.abspath(__file__))}/assets/icon.ico"))
        
    
    def main_page(self):
        uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/main.ui", self)
        
        # Connect the button to a method
        self.signup_button.clicked.connect(self.signup_action)
        self.login_button.clicked.connect(self.login_page)
        
    def signup_action(self):
        uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/signup.ui", self)
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_button.clicked.connect(lambda: signup(self.email.text(), self.username.text(), self.password.text(), self.confirm_password.text()))
        self.back_button.clicked.connect(self.main_page)
        self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))
        self.confirm_password_toggle.clicked.connect(lambda: self.toggle_password(self.confirm_password))
        

    def login_page(self):
        uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/login.ui", self)
        
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_button.clicked.connect(lambda: login(self.user.text(), self.password.text()))
        self.back_button.clicked.connect(self.main_page)
        self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))
        
        

    def verification_page(self, email):
        uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/verification.ui", self)
        self.verify_button.clicked.connect(lambda: verify(email, self.code.text()))
        self.send_again_button.clicked.connect(lambda: send_verification(email))
        self.back_button.clicked.connect(self.main_page)
        
    
    def send_verification_page(self):
        uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/send_verification.ui", self)
        self.send_code_button.clicked.connect(lambda: send_verification(self.email.text()))
        self.back_button.clicked.connect(self.main_page)
    
    
    def user_page(self):
        files = get_cwd_files()
        directories = get_cwd_directories()
        uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/user.ui", self)
        self.draw_cwd(files, directories)

        self.user_button.setText(user["username"])
        self.main_text.setText(f"Welcome {user["username"]}")
        
        self.user_button.clicked.connect(lambda: self.manage_account())
        self.logout_button.clicked.connect(logout)
        self.upload_button.clicked.connect(lambda: self.file_dialog())
        
    
    def draw_cwd(self, files, directories):
        x, y = 100, 150  # Initial position for the first button
        button_width, button_height = 100, 50
        spacing = 10  # Space between buttons

        for index, file_name in enumerate(files):
            # Create a QPushButton for each file
            button = QPushButton(file_name, self.centralwidget)

            # Set the position and size of the button
            button.setGeometry(x, y, button_width, button_height)
            button.setStyleSheet("background-color:darkgrey;font-size:12px;")

            # Connect the button to a function that handles button clicks
            button.clicked.connect(lambda checked, f=file_name: self.file_button_clicked(f))

            # Update x, y positions for the next button
            x += button_width + spacing  # Move to the right
            if x + button_width > self.width() - 100:  # Move to the next row if it exceeds window width
                x = 100
                y += button_height + spacing
        
        for index, directory in enumerate(directories):
            # Create a QPushButton for each file
            button = QPushButton(directory, self.centralwidget)

            # Set the position and size of the button
            button.setGeometry(x, y, button_width, button_height)
            button.setStyleSheet("background-color:brown;font-size:12px;")

            # Connect the button to a function that handles button clicks
            button.clicked.connect(lambda checked, d=directory: move_dir(d))

            # Update x, y positions for the next button
            x += button_width + spacing  # Move to the right
            if x + button_width > self.width() - 100:  # Move to the next row if it exceeds window width
                x = 100
                y += button_height + spacing
        
        button = QPushButton("/..", self.centralwidget)
        button.setGeometry(x, y, button_width, button_height)
        button.setStyleSheet("background-color:brown;font-size:12px;")
        button.clicked.connect(lambda: move_dir("/.."))
    
    
    
    
    
    def file_button_clicked(self, file_name):
        """Handle file button clicks."""
        print(f"File clicked: {file_name}")
    
    
    def manage_account(self):
        uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/account_managment.ui", self)
        
        self.forgot_password_button.clicked.connect(lambda: self.recovery(user["email"]))
        self.delete_account_button.clicked.connect(lambda: delete_user(user["email"]))
        
        self.back_button.clicked.connect(self.user_page)
    
    def recovery(self, email):
        reset_password(email)
        
        uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/recovery.ui", self)
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.back_button.clicked.connect(self.manage_account)
        self.reset_button.clicked.connect(lambda: password_recovery(email, self.code.text(), self.password.text(), self.confirm_password.text()))
        
        self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))
        self.confirm_password_toggle.clicked.connect(lambda: self.toggle_password(self.confirm_password))
        self.send_again_button.clicked.connect(lambda: reset_password(email))
        
    
    def toggle_password(self, text):
        if text.echoMode()==QLineEdit.EchoMode.Normal:
            text.setEchoMode(QLineEdit.EchoMode.Password)
        else:
            text.setEchoMode(QLineEdit.EchoMode.Normal)
    
    
    def file_dialog(self):
        # Open the file dialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Text Files (*.txt)")
        
        # If a file is selected, display its path in the label
        if file_name:
            #self.set_message(f'Selected File: {file_name}')
            send_file_data(file_name, file_name.split("/")[-1])
    
    def set_error_message(self, msg):
        if (hasattr(self, "error_message")):
            self.error_message.setStyleSheet("color: red; font-size: 15px;")
            self.error_message.setText(msg)
    
    def set_message(self, msg):
        if (hasattr(self, "message")):
            self.message.setStyleSheet("color: lightgreen; font-size: 15px;")
            self.message.setText(msg)




# Files functions
def send_file_data(copy_loc, save_loc):

    if(not os.path.isfile(copy_loc)):
        window.set_error_message(f"File path was not found")
        return

    size = os.path.getsize(copy_loc)
    left = size % chunk_size
    start_string = b'FILS|' + copy_loc.encode() + b'|' + save_loc.encode() + b'|' + str(size).encode()
    send_data(start_string)
    f = open(copy_loc, 'rb')
    for i in range(size//chunk_size):
        data = f.read(chunk_size)
        send_data(b"FILD" + data)
    data = f.read(left)
    if (data != b""):
        send_data(b'FILE' + data)
    f.close()
    handle_reply()


def move_dir(new_dir):
    send_data(f"MOVD{sep}{new_dir}".encode())
    handle_reply()



# Begin server requests related functions

def build_req_string(code, values = []):
    """
    Builds a request string
    Gets string code and list of string values
    """
    send_string = code
    for value in values:
        send_string += sep
        send_string += value
    return send_string.encode()

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
    window.verification_page(email)

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
    if(askyesno("Double Check", "Are you sure you want to delete your user?")):
        items = [email]
        send_string = build_req_string("DELU", items)
        send_data(send_string)
        handle_reply()

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
    try:
        to_show = 'Invalid reply from server'
        reply = reply.decode()   # Parse the reply and aplit it according to the protocol seperator
        fields = reply.split(sep)
        code = fields[0]
        if code == 'ERRR':   # If server returned error show to user the error
            err_code = int(fields[1])
            if (err_code not in error_messages):
                window.set_error_message(fields[2])
            else:
                error = error_messages[err_code].split("|")
                window.set_error_message(error[0] + " " + error[1])
                if(err_code == 10):
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
            
            window.user_page()
        
        elif code == 'SIGS':   # Signup was performed
            email = fields[1]
            username = fields[2]
            password = fields[3]
            to_show = f'Signup was successful for user: {username}, password:{password}'
            
            window.verification_page(email)
            window.set_message(f"Signup for user {username} completed. Verification code was sent to your email please verify your account")
            
        
        elif code == 'FOPR':   # Recovery mail sent
            to_show = f'Recovery email sent to: {fields[1]}'
        
        elif code == 'PASS':   # Password was reset
            new_pwd = fields[2]
            to_show = f'Password was reset for user: {fields[1]}, new password: {new_pwd}'
            window.main_page()
            window.set_message("Password reset successful, please sign in again with your new password")
        
        elif code == 'LUGR':   # Logout was performed
            to_show = f'Logout succesfull'
            window.main_page()
        
        elif code == 'VERS':   # Account verification mail sent
            email = fields[1]
            to_show = f'Verification sent to email {email}'
            window.verification_page(email)
        
        elif code == 'VERR':   # Verification succeeded
            username = fields[1]
            to_show = f'Verification for user {username} was succesfull'
            
            window.main_page()
            window.set_message(f"Verification for user {username} completed. You may now log in to your account")
        
        elif code == 'DELR':   # User deletion succeeded
            username = fields[1]
            to_show = f'User {username} was deleted'
            window.main_page()
        
        elif code == 'FILR':
            to_show = f'File {fields[1]} was uploaded'
            window.user_page()
            window.set_message(to_show)
        
        elif code == 'MOVR':
            to_show = f'Directory {fields[1]} was moved into'
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
        if to_show == "Server acknowledged the exit message":   # If exit request succeded, dissconnect
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
    
    sock.send(to_send)

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
        
        return msg
    
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
        with open(f"{os.path.dirname(os.path.abspath(__file__))}/gui/css/style.css", 'r') as f:
            app.setStyleSheet(f.read())
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
        
        
    except Exception as e:
        print("Error:" + str(e))
        print(traceback.format_exc())

if __name__ == "__main__":   # Run main
    main(("127.0.0.1", 31026))
