# 2024 © Idan Hazay
# Import libraries

from modules import encrypting
from modules.dialogs import *
from modules.helper import *
from modules.limits import Limits
from modules.logger import Logger
from modules.file_viewer import *

import socket
import sys
import traceback
import rsa
import struct
import os
import threading

from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout, QPushButton, QCheckBox, QFileDialog, QLineEdit, QGridLayout, QScrollArea, QHBoxLayout, QSpacerItem, QSizePolicy, QMenu, QInputDialog
from PyQt6.QtGui import QIcon, QContextMenuEvent, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import QSize


# Announce global vars
len_field = 4
user = {"email": "guest", "username": "guest", "subscription_level": 0, "cwd": "", "parent_cwd": "", "cwd_name": ""}
encryption = False
chunk_size = 65536
used_storage = 0
user_icon = f"{os.path.dirname(os.path.abspath(__file__))}/assets/user.ico"
assets_path = f"{os.path.dirname(os.path.abspath(__file__))}/assets"
cookie_path = f"{os.path.dirname(os.path.abspath(__file__))}/cookies/user.cookie"
log = False
search_filter = None
share = False
sort = "Name"

# Begin gui related functions

class FileButton(QPushButton):
    def __init__(self, text, id = None, parent=None, is_folder = False, shared_by = None, perms =["True", "True","True","True","True","True"]):
        super().__init__(text, parent)
        self.id = id
        self.is_folder = is_folder
        self.shared_by = shared_by
        self.perms = perms
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
        
        if self.id != None and self.perms[4] == "True":
            action = menu.addAction(" Download")
            action.triggered.connect(self.download)
            action.setIcon(QIcon(assets_path + "\\download.svg"))

        if self.id != None:
            if self.perms[2] == "True":
                action = menu.addAction(" Delete")
                action.triggered.connect(self.delete)
                action.setIcon(QIcon(assets_path + "\\delete.svg"))

            if self.perms[3] == "True":
                action = menu.addAction(" Rename")
                action.triggered.connect(self.rename)
                action.setIcon(QIcon(assets_path + "\\change_user.svg"))
            
            if self.perms[5] == "True":
                action = menu.addAction(" Share")
                action.triggered.connect(self.share)
                action.setIcon(QIcon(assets_path + "\\share.svg"))
            
            if share and user["cwd"] == "":
                action = menu.addAction(" Remove")
                action.triggered.connect(self.remove)
                action.setIcon(QIcon(assets_path + "\\remove.svg"))

        if not share:
            action = menu.addAction(" New Folder")
            action.triggered.connect(new_folder)
            action.setIcon(QIcon(assets_path + "\\new_account.svg"))
            #action.setEnabled(False)

        action = menu.addAction(" Search")
        action.triggered.connect(search)
        action.setIcon(QIcon(assets_path + "\\search.svg"))

        menu.exec(event.globalPos())

    def download(self):
        file_name = self.text().split(" | ")[0][1:]
        if self.is_folder: file_path, _ = QFileDialog.getSaveFileName(self, "Save File", file_name, "Zip Files (*.zip);;All Files (*)")
        else: file_path, _ = QFileDialog.getSaveFileName(self, "Save File", file_name, "Text Files (*.txt);;All Files (*)")
        if file_path:
            send_data(b"DOWN|" + self.id.encode())
            save_file(file_path)

    def rename(self):
        name = self.text().split(" | ")[0][1:]
        new_name = new_name_dialog("Rename", "Enter new file name:", name)
        if new_name is not None:
            send_data(b"RENA|" + self.id.encode() + b"|" + name.encode() + b"|" + new_name.encode())
            handle_reply()

    def delete(self):
        name = self.text().split(" | ")[0][1:]
        if show_confirmation_dialog("Are you sure you want to delete " + name):
            send_data(b"DELF|" + self.id.encode())
            handle_reply()

    def share(self):
        name = self.text().split(" | ")[0][1:]
        user_email = new_name_dialog("Share", f"Enter email/username of the user you want to share {name} with:")
        if user_email is not None:
            send_data(b"SHRS|" + self.id.encode() + b"|" + user_email.encode())
            handle_reply()
    
    def remove(self):
        send_data(B"SHRE|" + self.id.encode())
        handle_reply()


def new_folder():
    new_folder = new_name_dialog("New Folder", "Enter new folder name:")
    if new_folder is not None:
        send_data(b"NEWF|" + new_folder.encode())
        handle_reply()


def search():
    global search_filter
    search_filter = new_name_dialog("Search", "Enter search filter:", search_filter)
    window.user_page()



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_page()
        if (os.path.isfile(f"{os.path.dirname(os.path.abspath(__file__))}/assets/icon.ico")):
            self.setWindowIcon(QIcon(f"{os.path.dirname(os.path.abspath(__file__))}/assets/icon.ico"))

        self.setFixedSize(1000, 550)
    

        
    def main_page(self):
        try:
            uic.loadUi(
                f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/main.ui", self)

            self.signup_button.clicked.connect(self.signup_page)
            self.signup_button.setIcon(QIcon(assets_path+"\\new_account.svg"))

            self.login_button.clicked.connect(self.login_page)
            self.login_button.setIcon(QIcon(assets_path+"\\login.svg"))

            self.exit_button.clicked.connect(exit_program)
            self.exit_button.setIcon(QIcon(assets_path+"\\exit.svg"))

        except:
            print(traceback.format_exc())

    def signup_page(self):
        try:
            uic.loadUi(
                f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/signup.ui", self)

            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

            self.password_toggle.clicked.connect(
                lambda: self.toggle_password(self.password))
            self.confirm_password_toggle.clicked.connect(
                lambda: self.toggle_password(self.confirm_password))

            self.signup_button.clicked.connect(lambda: signup(self.email.text(
            ), self.username.text(), self.password.text(), self.confirm_password.text()))
            self.signup_button.setShortcut("Return")
            self.signup_button.setIcon(QIcon(assets_path+"\\new_account.svg"))

            self.login_button.clicked.connect(self.login_page)
            self.login_button.setStyleSheet("background-color:transparent;color:royalblue;text-decoration: underline;font-size:14px;border:none;")

            self.back_button.clicked.connect(self.main_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
        except:
            print(traceback.format_exc())

    def login_page(self):
        try:
            uic.loadUi(
                f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/login.ui", self)
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))
            self.forgot_password_button.clicked.connect(self.forgot_password)
            self.forgot_password_button.setStyleSheet("background-color:transparent;color:royalblue;text-decoration: underline;font-size:14px;border:none;")

            self.signup_button.clicked.connect(self.signup_page)
            self.signup_button.setStyleSheet("background-color:transparent;color:royalblue;text-decoration: underline;font-size:14px;border:none;")

            self.login_button.clicked.connect(lambda: login(self.user.text(), self.password.text(), self.remember.isChecked()))
            self.login_button.setShortcut("Return")
            self.login_button.setIcon(QIcon(assets_path+"\\login.svg"))

            self.back_button.clicked.connect(self.main_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
        except:
            print(traceback.format_exc())

    def forgot_password(self):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/forgot_password.ui", self)
            self.send_code_button.clicked.connect(
                lambda: reset_password(self.email.text()))
            self.send_code_button.setShortcut("Return")
            self.send_code_button.setIcon(QIcon(assets_path+"\\send.svg"))

            self.back_button.clicked.connect(self.login_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
        except:
            print(traceback.format_exc())

    def verification_page(self, email):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(
                __file__))}/gui/ui/verification.ui", self)
            self.verify_button.clicked.connect(lambda: verify(email, self.code.text()))
            self.verify_button.setShortcut("Return")
            self.verify_button.setIcon(QIcon(assets_path+"\\verify.svg"))

            self.send_again_button.clicked.connect(
                lambda: send_verification(email))
            self.send_again_button.setIcon(QIcon(assets_path+"\\again.svg"))

            self.back_button.clicked.connect(self.main_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
        except:
            print(traceback.format_exc())

    def send_verification_page(self):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/send_verification.ui", self)
            self.send_code_button.clicked.connect(
                lambda: send_verification(self.email.text()))
            self.send_code_button.setShortcut("Return")
            self.send_code_button.setIcon(QIcon(assets_path+"\\send.svg"))

            self.back_button.clicked.connect(self.main_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
        except:
            print(traceback.format_exc())

    def user_page(self):
        try:
            if user["cwd"] == "" and share: 
                files = get_cwd_shared_files(search_filter)
                directories = get_cwd_shared_directories(search_filter)
            else:
                files = get_cwd_files(search_filter)
                directories = get_cwd_directories(search_filter)
            
            
            get_used_storage()

            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/user.ui", self)
            self.setAcceptDrops(True)
            self.set_cwd()
            
            if sort ==  "Name":
                self.sort.setCurrentIndex(0)
                files = sorted(files, key=lambda x: x.split("~")[0])
                directories = sorted(directories, key=lambda x: x.split("~")[0])
            elif sort == "Date":
                self.sort.setCurrentIndex(1)
                files = sorted(files, key=lambda x: x.split("~")[1])
            elif sort == "Type":
                self.sort.setCurrentIndex(2)
                files = sorted(files, key=lambda x: x.split("~")[0].split(".")[-1])
            elif sort == "Size":
                self.sort.setCurrentIndex(3)
                files = sorted(files, key=lambda x: int(x.split("~")[2]))
                
            self.draw_cwd(files, directories)

            self.main_text.setText(f"Welcome {user["username"]}")

            self.storage_label.setText(f"Storage used ({format_file_size(used_storage*1_000_000)} / {Limits(user["subscription_level"]).max_storage//1000} GB):")
            self.storage_remaining.setMaximum(Limits(user["subscription_level"]).max_storage)
            self.storage_remaining.setValue(int(used_storage))

            self.search.setIcon(QIcon(assets_path+"\\search.svg"))
            self.search.setText(f"Search Filter: {search_filter}")
            self.search.clicked.connect(search)
            self.search.setStyleSheet("background-color:transparent;font-size:13px;border:none;")
            
            self.shared_button.clicked.connect(change_share)
            self.shared_button.setIcon(QIcon(assets_path+"\\share.svg"))
            if share:
                try: self.shared_button.setIcon((QIcon(user_icon)))
                except: pass
                self.shared_button.setText(" Your files")
                self.upload_button.hide()

            self.sort.currentIndexChanged.connect(lambda: change_sort(self.sort.currentText()[1:]))
        
            
            self.user_button.clicked.connect(lambda: self.manage_account())
            self.logout_button.clicked.connect(logout)
            self.logout_button.setIcon(QIcon(assets_path+"\\logout.svg"))
            self.upload_button.clicked.connect(lambda: self.file_dialog())
            self.upload_button.setIcon(QIcon(assets_path+"\\upload.svg"))
            self.user_button.setFixedSize(50, 50)
            self.user_button.setIconSize(QSize(40, 40))
            self.user_button.setStyleSheet("padding:0px;border-radius:5px;")
            
            try:
                self.user_button.setIcon((QIcon(user_icon)))
            except:
                pass
        except:
            print(traceback.format_exc())
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():  # Check if the dragged object is a file (URL)
            event.acceptProposedAction()  # Accept the drag event
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
            for file_path in file_paths:
                file_name = file_path.split("/")[-1]
                start_string = b'FILS|' + file_name.encode() + b"|" + user["cwd"].encode()
                send_data(start_string)
                send_file(file_path)
                #self.set_message(f"{len(file_paths)} file(s) dropped: {', '.join([fp.split('/')[-1] for fp in file_paths])}")

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
                file = file.split("~")
                file_name = file[0]
                date = file[1][:-7]
                size = format_file_size(int(file[2]))
                file_id = file[3]
                perms = file[5:]
                if share:
                    button = FileButton(f" {file_name} | {date} | {size} | From {file[4]}", file_id, shared_by=file[4], perms=perms)
                else:
                    button = FileButton(f" {file_name} | {date} | {size}", file_id)
                button.setStyleSheet("background-color:dimgrey;border:1px solid darkgrey;font-size:14px;border-radius: 3px;")
                button.clicked.connect(lambda checked, name=file_name, id = file_id: view_file(id, name))
                button.setIcon(QIcon(assets_path + "\\file.svg"))
                scroll_layout.addWidget(button)

            for index, directory in enumerate(directories):
                directory = directory.split("~")
                perms = directory[3:]
                if share:
                    button = FileButton(f" {directory[0]} | From {directory[2]}", directory[1], is_folder=True, shared_by=directory[2], perms=perms)
                else:
                    button = FileButton(f" {directory[0]}", directory[1], is_folder=True)
                button.setStyleSheet("background-color:peru;font-size:14px;border-radius: 3px;border:1px solid peachpuff;")
                button.clicked.connect(lambda checked, id=directory[1]: move_dir(id))
                button.setIcon(QIcon(assets_path + "\\folder.svg"))
                scroll_layout.addWidget(button)

            if (directories == [] and files == []):
                button = FileButton("No files or folders in this directory")
                button.setStyleSheet(
                    "background-color:red;font-size:14px;border-radius: 3px;border:1px solid darkgrey;")
                scroll_layout.addWidget(button)

            if (user["cwd"] != ""):
                button = FileButton("Back")
                button.setStyleSheet("background-color:green;font-size:14px;border-radius: 3px;border:1px solid lightgreen;")
                button.clicked.connect(lambda: move_dir(user["parent_cwd"]))
                scroll_layout.addWidget(button)

            scroll_container_widget.setLayout(scroll_layout)

            scroll.setWidget(scroll_container_widget)
            scroll.setFixedSize(QSize(900, 340))
            spacer = QSpacerItem(
                20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
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

            self.forgot_password_button.clicked.connect(
                lambda: reset_password(user["email"]))
            self.forgot_password_button.setIcon(
                QIcon(assets_path + "\\key.svg"))

            self.delete_account_button.clicked.connect(
                lambda: delete_user(user["email"]))
            self.delete_account_button.setIcon(
                QIcon(assets_path + "\\delete.svg"))

            self.upload_icon_button.clicked.connect(lambda: upload_icon())
            self.upload_icon_button.setIcon(
                QIcon(assets_path + "\\profile.svg"))

            self.subscriptions_button.clicked.connect(self.subscriptions_page)
            self.subscriptions_button.setIcon(
                QIcon(assets_path + "\\upgrade.svg"))

            self.change_username_button.clicked.connect(change_username)
            self.change_username_button.setIcon(
                QIcon(assets_path + "\\change_user.svg"))

            self.back_button.clicked.connect(self.user_page)
            self.back_button.setIcon(
                QIcon(assets_path + "\\back.svg"))
        except:
            print(traceback.format_exc())

    def subscriptions_page(self):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/subscription.ui", self)

            get_used_storage()
            self.back_button.clicked.connect(self.manage_account)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))

            self.free_button.clicked.connect(lambda: subscribe(0))
            self.basic_button.clicked.connect(lambda: subscribe(1))
            self.premium_button.clicked.connect(lambda: subscribe(2))
            self.professional_button.clicked.connect(lambda: subscribe(3))

            if user["subscription_level"] == "0":
                self.free_button.setDisabled(True)
                self.free_button.setText("Selected")
                self.free_button.setStyleSheet("background-color:dimgrey")
            elif user["subscription_level"] == "1":
                self.basic_button.setDisabled(True)
                self.basic_button.setText("Selected")
                self.basic_button.setStyleSheet("background-color:dimgrey")
            elif user["subscription_level"] == "2":
                self.premium_button.setDisabled(True)
                self.premium_button.setText("Selected")
                self.premium_button.setStyleSheet("background-color:dimgrey")
            elif user["subscription_level"] == "3":
                self.professional_button.setDisabled(True)
                self.professional_button.setText("Selected")
                self.professional_button.setStyleSheet(
                    "background-color:dimgrey")

            self.storage_remaining.setMaximum(
                Limits(user["subscription_level"]).max_storage)
            self.storage_remaining.setValue(int(used_storage))
            self.storage_label.setText(
                f"Storage used ({format_file_size(used_storage*1_000_000)} / {Limits(user["subscription_level"]).max_storage//1000} GB):")

        except:
            print(traceback.format_exc())

    def recovery(self, email):
        try:
            uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/gui/ui/recovery.ui", self)
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

            self.password_toggle.clicked.connect(
                lambda: self.toggle_password(self.password))
            self.confirm_password_toggle.clicked.connect(
                lambda: self.toggle_password(self.confirm_password))

            self.reset_button.clicked.connect(lambda: password_recovery(email, self.code.text(), self.password.text(), self.confirm_password.text()))
            self.reset_button.setShortcut("Return")
            self.reset_button.setIcon(QIcon(assets_path+"\\reset.svg"))

            self.send_again_button.clicked.connect(
                lambda: reset_password(email))
            self.send_again_button.setIcon(QIcon(assets_path+"\\again.svg"))

            self.back_button.clicked.connect(self.manage_account)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
        except:
            print(traceback.format_exc())

    def toggle_password(self, text):
        if text.echoMode() == QLineEdit.EchoMode.Normal:
            text.setEchoMode(QLineEdit.EchoMode.Password)
        else:
            text.setEchoMode(QLineEdit.EchoMode.Normal)

    def file_dialog(self):
        try:
            file_paths, _ = QFileDialog.getOpenFileNames(self, "Open File", "", "All Files (*);;Text Files (*.txt)")

            if file_paths:  # Check if any files were selected
                for file_path in file_paths:
                    file_name = file_path.split("/")[-1]  # Extract the file name
                    start_string = b'FILS|' + file_name.encode() + b"|" + user["cwd"].encode()
                    # Assuming send_data and send_file are defined elsewhere
                    send_data(start_string)
                    send_file(file_path)  # Send the selected file
                #self.set_message(f"{len(file_paths)} file(s) uploaded: {', '.join([fp.split('/')[-1] for fp in file_paths])}")
        except:
            print(traceback.format_exc())
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():  # Check if the dragged object is a file (URL)
            event.acceptProposedAction()  # Accept the drag event

    # This function handles when the dragged object is dropped
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
            for file_path in file_paths:
                file_name = file_path.split("/")[-1]
                start_string = b'FILS|' + file_name.encode() + b"|" + user["cwd"].encode()
                send_data(start_string)
                send_file(file_path)
            #self.set_message(f"{len(file_paths)} file(s) dropped: {', '.join([fp.split('/')[-1] for fp in file_paths])}")

    
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
            if share: self.cwd.setText(f"CWD: Shared\\{user['cwd_name']}")
            else: self.cwd.setText(f"CWD: {user['username']}\\{user['cwd_name']}")


# Files functions
def send_file(file_path):
    if (not os.path.isfile(file_path)):
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
                return
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
                    return protocol_parse_reply(data)
                data = b''
    except:
        print(traceback.format_exc())
        handle_reply()
    handle_reply()


def view_file(file_id, file_name):
    send_data(b"VIEW|" + file_id.encode())
    save_path = f"{os.path.dirname(os.path.abspath(__file__))}\\temp-{file_name}"
    response = save_file(save_path)
    if response is not None:
        os.remove(save_path)
        return
    result = file_viewer_dialog("File Viewer", save_path)
    if result:
        print("File viewer opened and closed successfully.")
    else:
        print("File viewer did not function as expected.")

    os.remove(save_path)


def change_share():
    global share
    share = not share
    move_dir("")

def change_sort(new_sort):
    global sort
    sort = new_sort
    window.user_page()

def move_dir(new_dir):
    send_data(f"MOVD|{new_dir}".encode())
    handle_reply()


def get_user_icon():
    send_data(b"GICO")
    save_file(user_icon)


def get_used_storage():
    send_data(b"GEUS")
    handle_reply()


def upload_icon():
    try:
        file_path, _ = QFileDialog.getOpenFileName(
            window, "Open File", "", "Icon Files (*.ico);")

        if file_path:
            file_name = file_path.split("/")[-1]
            start_string = b'ICOS|' + file_name.encode()

            send_data(start_string)
            send_file(file_path)
    except:
        print(traceback.format_exc())



def change_username():
    name = user["username"]
    new_name = new_name_dialog("Change Username", "Enter new  username:", name)
    if new_name is not None and new_name != name:
        send_data(b"CHUN|" + new_name.encode())
        handle_reply()


def subscribe(level):
    send_data(b"SUBL|" + str(level).encode())
    handle_reply()


def share_file(file_id, user_cred, read = False, write = False, delete = False, rename = False, download = False, share = False):
    app = QApplication.instance()  # Use existing QApplication
    if app is None:
        app = QApplication([])  # Create a new instance if it doesn't exist

    dialog = QDialog()
    layout = QVBoxLayout()
    dialog.setWindowTitle("File Share Options")
    dialog.resize(600, 400)
        
    read_cb = QCheckBox("Read")
    read_cb.setChecked(read == "True")
        
    write_cb = QCheckBox("Write")
    write_cb.setChecked(write == "True")
        
    delete_cb = QCheckBox("Delete")
    delete_cb.setChecked(delete == "True")
        
    rename_cb = QCheckBox("Rename")
    rename_cb.setChecked(rename == "True")
        
    download_cb = QCheckBox("Download")
    download_cb.setChecked(download == "True")
        
    share_cb = QCheckBox("Share")
    share_cb.setChecked(share == "True")

    # Submit button
    submit_btn = QPushButton("Submit")
    submit_btn.setShortcut("Return")
    submit_btn.clicked.connect(lambda: send_share_premissions(dialog, file_id, user_cred, read_cb.isChecked(), write_cb.isChecked(), delete_cb.isChecked(), rename_cb.isChecked(), download_cb.isChecked(), share_cb.isChecked()))

        # Layout setup
    layout = QVBoxLayout()
    layout.addWidget(read_cb)
    layout.addWidget(write_cb)
    layout.addWidget(delete_cb)
    layout.addWidget(rename_cb)
    layout.addWidget(download_cb)
    layout.addWidget(share_cb)
    layout.addWidget(submit_btn)
    dialog.setLayout(layout)
    dialog.exec()

def send_share_premissions(dialog, file_id, user_cred, read, write, delete, rename, download, share):
    dialog.accept()
    to_send = f"SHRP|{file_id}|{user_cred}|{read}|{write}|{delete}|{rename}|{download}|{share}"
    send_data(to_send.encode())
    handle_reply()

# Begin server requests related functions


def login(cred, password, remember):
    """
    Send login request to server
    """
    items = [cred, password]
    send_string = build_req_string("LOGN", items)
    send_data(send_string)
    handle_reply()
    if remember and (user["email"] == cred or user["username"] == cred):
        send_data(b"GENC")
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
    if (confirm_account_deletion(email)):
        items = [email]
        send_string = build_req_string("DELU", items)
        send_data(send_string)
        handle_reply()


def confirm_account_deletion(email):
    # Create a QApplication instance if needed
    confirm_email = new_name_dialog("Delete Account", "Enter account email:")
    if email == confirm_email:
        return True
    else:
        window.set_error_message("Entered email does not match account email")



def exit_program():
    """
    Send exit request to server
    """
    send_string = build_req_string("EXIT")
    send_data(send_string)
    handle_reply()


def get_cwd_files(filter=None):
    to_send = b"GETP" + b"|" + user["cwd"].encode()
    if filter:
        to_send += b"|" + filter.encode()
    send_data(to_send)
    data = recv_data()
    try:
        if (data[:4] != b"PATH"):
            return []
        data = data.decode()
        return data.split("|")[1:]
    except Exception:
        print(traceback.format_exc())
        return []

def get_cwd_shared_files(filter=None):
    to_send = b"GESP" + b"|" + user["cwd"].encode()
    if filter:
        to_send += b"|" + filter.encode()
    send_data(to_send)
    data = recv_data()
    try:
        if (data[:4] != b"PASH"):
            return []
        data = data.decode()
        return data.split("|")[1:]
    except Exception:
        print(traceback.format_exc())
        return []


def get_cwd_directories(filter=None):
    to_send = b"GETD" + b"|" + user["cwd"].encode()
    if filter:
        to_send += b"|" + filter.encode()
    send_data(to_send)
    data = recv_data()
    try:
        if (data[:4] != b"PATD"):
            return []
        data = data.decode()
        return data.split("|")[1:]
    except Exception:
        print(traceback.format_exc())
        return []

def get_cwd_shared_directories(filter=None):
    to_send = b"GESD" + b"|" + user["cwd"].encode()
    if filter:
        to_send += b"|" + filter.encode()
    send_data(to_send)
    data = recv_data()
    try:
        if (data[:4] != b"PASD"):
            return []
        data = data.decode()
        return data.split("|")[1:]
    except Exception:
        print(traceback.format_exc())
        return []

def save_cookie(cookie):
    with open(cookie_path, "w") as f:
        f.write(cookie)

def send_cookie():
    try:
        with open(cookie_path, "r") as f:
            cookie = f.read()
            send_data(b"COKE|" + cookie.encode())
            handle_reply()
    except:
        pass
    
    
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
    while (len(key_len_b) < len_field):   # Recieve the length of the key
        key_len_b += sock.recv(len_field - len(key_len_b))
    key_len = int(struct.unpack("!l", key_len_b)[0])

    key_binary = b""
    while (len(key_binary) < key_len):   # Recieve the key according to its length
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
        if reply == None:
            return None
        # Parse the reply and aplit it according to the protocol seperator
        reply = reply.decode()
        fields = reply.split("|")
        code = fields[0]
        if code == 'ERRR':   # If server returned error show to user the error
            err_code = int(fields[1])
            window.set_error_message(fields[2])
            if (err_code == 9):
                window.send_verification_page()

            to_show = 'Server return an error: ' + fields[1] + ' ' + fields[2]

        # Handle each response accordingly
        elif code == 'EXTR':   # Server exit success
            to_show = 'Server acknowledged the exit message'

        elif code == 'LOGS':   # Login succeeded
            email = fields[1]
            username = fields[2]
            to_show = f'Login was succesfull for user: {username}'
            user["email"] = email
            user["username"] = username
            user["subscription_level"] = fields[3]
            get_user_icon()
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
            logout()
            window.main_page()
            window.set_message("Password reset successful, please sign in again with your new password")

        elif code == 'LUGR':   # Logout was performed
            global share
            user["email"] = "guest"
            user["username"] = "guest"
            user["subscription_level"] = 0
            user["cwd"] = ""
            user["parent_cwd"] = ""
            user["cwd_name"] = ""
            share = False
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
            user["cwd"] = fields[1]
            user["parent_cwd"] = fields[2]
            user["cwd_name"] = fields[3]
            to_show = f'Succesfully moved to {fields[3]}'
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

        elif code == 'SUBR':
            level = fields[1]
            user["subscription_level"] = level
            sub = "free"
            if level == "1":
                sub = "basic"
            if level == "2":
                sub = "premium"
            if level == "3":
                sub = "professional"
            to_show = f"Subscription level updated to {sub}"
            window.subscriptions_page()
            window.set_message(to_show)

        elif code == 'GEUR':
            global used_storage
            used_storage = round(int(fields[1])/1_000_000, 3)
            to_show = f"Current used storage is {used_storage}"

        elif code == 'CHUR':
            new_username = fields[1]
            user["username"] = new_username
            to_show = f"Username changed to {new_username}"
            window.manage_account()
            window.set_message(to_show)
        elif code == 'VIER':
            file_name = fields[1]
            to_show = f"File {file_name} was viewed"
            window.set_message(to_show)
        elif code == 'COOK':
            cookie = fields[1]
            save_cookie(cookie)
            to_show = f"Cookie recieved"
        elif code == "SHRR":
            file_id = fields[1]
            user_cred = fields[2]
            if len(fields) == 3:
                share_file(file_id, user_cred)
            else:
                share_file(file_id, user_cred, *fields[3:])
            to_show = "Sharing options recieved"
        elif code == "SHPR":
            to_show = fields[1]
            window.set_message(to_show)
        elif code == "SHRM":
            name = fields[1]
            to_show = f"Succefully remove {name} from share"
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
        # If exit request succeded, dissconnect
        if to_show == "Server acknowledged the exit message" or to_show == None:
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

        if (encryption):  # If encryption is enabled decrypt and log encrypted
            logtcp('recv', b_len + msg)   # Log encrypted data
            msg = encrypting.decrypt(msg, shared_secret)
            logtcp('recv', str(msg_len).encode() + msg)

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
        # gui.create_root()

        app = QtWidgets.QApplication(sys.argv)
        with open(f"{os.path.dirname(os.path.abspath(__file__))}/gui/css/style.css", 'r') as f: app.setStyleSheet(f.read())
        window = MainWindow()
        window.show()
        send_cookie()
        sys.exit(app.exec())

    except Exception as e:
        print("Error:" + str(e))
        print(traceback.format_exc())


if __name__ == "__main__":   # Run main
    #sys.stdout = Logger()
    ip = "127.0.0.1"
    if len(sys.argv) == 2:
        ip = sys.argv[1]

    main((ip, 31026))
