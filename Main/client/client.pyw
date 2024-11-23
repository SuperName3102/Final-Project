# 2024 © Idan Hazay
# Import libraries

from modules.dialogs import *
from modules.helper import *
from modules.limits import Limits
from modules.logger import Logger
from modules.file_viewer import *
from modules.networking import *
from modules.key_exchange import *

import socket, sys, traceback, os, uuid

from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout, QPushButton, QCheckBox, QGroupBox, QFileDialog, QLineEdit, QGridLayout, QScrollArea, QHBoxLayout, QSpacerItem, QSizePolicy, QMenu
from PyQt6.QtGui import QIcon, QContextMenuEvent, QDragEnterEvent, QDropEvent, QMoveEvent, QFont
from PyQt6.QtCore import QSize,  QRect, QThread, pyqtSignal


# Announce global vars
user = {"email": "guest", "username": "guest", "subscription_level": 0, "cwd": "", "parent_cwd": "", "cwd_name": ""}
chunk_size = 65536
used_storage = 0
user_icon = f"{os.getcwd()}/assets/user.ico"
assets_path = f"{os.getcwd()}/assets"
cookie_path = f"{os.getcwd()}/cookies/user.cookie"

search_filter = None
share = False
deleted = False
sort = "Name"
remember = False

window_geometry = QRect(350, 200, 1000, 550)
original_sizes = {}
active_threads = []
file_queue = []
scroll = None
scroll_size = [850, 340]

dont_send = False
ip = "127.0.0.1"
port = 31026

files = []
directories = []
files_downloading = {}

last_msg = ""
last_error_msg = ""

# Begin gui related functions
class File():
    def __init__(self, save_location, id, size, is_view = False):
        self.save_location = save_location
        self.id = id
        self.size = size
        self.is_view = is_view
        self.start_download()
    
    def start_download(self):
        with open(self.save_location, 'wb') as f:
            f.write(b"\0")
            f.flush()
    
    def add_data(self, data, location_infile):
        try:
            with open(self.save_location, 'r+b') as f:
                f.seek(location_infile)
                f.write(data)
                f.flush()
        except:
            self.uploading = False
    
    def delete(self):
        if os.path.exists(self.save_location): os.remove(self.save_location)


class FileButton(QPushButton):
    def __init__(self, text, id = None, parent=None, is_folder = False, shared_by = None, perms =["True", "True","True","True","True","True"]):
        super().__init__("|".join(text), parent)
        self.setText = "|".join(text)
        self.id = id
        self.is_folder = is_folder
        self.shared_by = shared_by
        self.perms = perms
        self.setMinimumHeight(30)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to align with button edges
        button_layout.setSpacing(0)
        for i, label_text in enumerate(text):
            label = QLabel(label_text)
            if i == 0:
                if self.is_folder:
                    label.setText(f'&nbsp;<img src="{assets_path + "\\folder.svg"}" width="20" height="20"><label>&nbsp;{truncate_label(label, label_text)}</label>')
                elif self.id is not None:
                    icon_path = assets_path + "\\file_types\\" + format_file_type(label_text.split("~")[0].split(".")[-1][:-1]) + ".svg"
                    if not os.path.isfile(icon_path): icon_path = assets_path + "\\file.svg"
                    label.setText(f'&nbsp;<img src="{icon_path}" width="16" height="20">&nbsp;{truncate_label(label, label_text)}')
            if self.id is None: label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if self.is_folder: label.setObjectName("folder-label")
            elif self.id != None: label.setObjectName("file-label")
            elif label_text == "Back": label.setObjectName("back-label")
            button_layout.addWidget(label, stretch=1)
        button_layout.setStretch(0, 2)  # First label takes 2 parts
        for i in range(1, len(text)):
            button_layout.setStretch(i, 1)  # Other labels take 1 part each

        self.setLayout(button_layout)

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)
        
        if self.id != None and self.perms[4] == "True" and not deleted:
            action = menu.addAction(" Download")
            action.triggered.connect(self.download)
            action.setIcon(QIcon(assets_path + "\\download.svg"))

        if self.id != None:
            if self.perms[2] == "True":
                if deleted and user["cwd"] != "": pass
                else:
                    action = menu.addAction(" Delete")
                    action.triggered.connect(self.delete)
                    action.setIcon(QIcon(assets_path + "\\delete.svg"))

            if self.perms[3] == "True" and not deleted:
                action = menu.addAction(" Rename")
                action.triggered.connect(self.rename)
                action.setIcon(QIcon(assets_path + "\\change_user.svg"))
            
            if self.perms[5] == "True" and not deleted:
                action = menu.addAction(" Share")
                action.triggered.connect(self.share)
                action.setIcon(QIcon(assets_path + "\\share.svg"))
            
            if share and user["cwd"] == "" and not deleted:
                action = menu.addAction(" Remove")
                action.triggered.connect(self.remove)
                action.setIcon(QIcon(assets_path + "\\remove.svg"))

        if not share and not deleted:
            action = menu.addAction(" New Folder")
            action.triggered.connect(new_folder)
            action.setIcon(QIcon(assets_path + "\\new_account.svg"))
        
        if deleted and user["cwd"] == "":
            action = menu.addAction(" Recover")
            action.triggered.connect(self.recover)
            action.setIcon(QIcon(assets_path + "\\new_account.svg"))

        action = menu.addAction(" Search")
        action.triggered.connect(search)
        action.setIcon(QIcon(assets_path + "\\search.svg"))

        menu.exec(event.globalPos())

    def download(self):
        file_name = self.text().split(" | ")[0][1:]
        if self.is_folder: 
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", file_name, "Zip Files (*.zip);;All Files (*)")
        else: 
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", file_name, "Text Files (*.txt);;All Files (*)")
        if file_path:
            send_data(b"DOWN|" + self.id.encode())
            files_downloading[self.id] = File(file_path, self.id, 0)
            

    def rename(self):
        name = self.text().split(" | ")[0][1:]
        new_name = new_name_dialog("Rename", "Enter new file name:", name)
        if new_name is not None:
            send_data(b"RENA|" + self.id.encode() + b"|" + name.encode() + b"|" + new_name.encode())

    def delete(self):
        name = self.text().split(" | ")[0][1:]
        if show_confirmation_dialog("Are you sure you want to delete " + name):
            send_data(b"DELF|" + self.id.encode())

    def share(self):
        name = self.text().split(" | ")[0][1:]
        user_email = new_name_dialog("Share", f"Enter email/username of the user you want to share {name} with:")
        if user_email is not None:
            send_data(b"SHRS|" + self.id.encode() + b"|" + user_email.encode())
    
    def remove(self):
        send_data(B"SHRE|" + self.id.encode())
    
    def recover(self):
        send_data(b"RECO|" + self.id.encode())


def new_folder():
    new_folder = new_name_dialog("New Folder", "Enter new folder name:")
    if new_folder is not None:
        send_data(b"NEWF|" + new_folder.encode())


def search():
    global search_filter
    search_filter = new_name_dialog("Search", "Enter search filter:", search_filter)
    window.user_page()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        if (os.path.isfile(f"{os.getcwd()}/assets/icon.ico")):
            self.setWindowIcon(QIcon(f"{os.getcwd()}/assets/icon.ico"))
        self.save_sizes()
        self.setGeometry(window_geometry)
        self.original_width = self.width()
        self.original_height = self.height()
        self.scroll_progress = 0
        s_width = app.primaryScreen().geometry().width()
        s_height = app.primaryScreen().geometry().height()
        self.resize(s_width*3//4, s_height*2//3)
        self.move(s_width//8, s_height//6)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WidgetAttribute.WA_PaintOnScreen, True)

    def save_sizes(self):
        for widget in self.findChildren(QWidget):
            # Save both the original geometry and the original font size (if the widget has a font)
            font_size = widget.font().pointSize()
            original_sizes[widget] = {
                'geometry': widget.geometry(),
                'font_size': font_size
            }
    
    def moveEvent(self, event: QMoveEvent):
        global window_geometry
        window_geometry = self.geometry()
    
    def resizeEvent(self, event):
        # Get the new window size
        global window_geometry, scroll, scroll_size
        new_width = self.width()
        new_height = self.height()

        # Calculate the scaling factors for width and height
        width_ratio = new_width / self.original_width
        height_ratio = new_height / self.original_height
        
        # Resize all child widgets based on the scaling factor
        
        for widget in self.findChildren(QWidget):
            if widget in original_sizes.keys():
                original_geometry = original_sizes[widget]['geometry']
                original_font_size = original_sizes[widget]['font_size']
                if width_ratio != 1:
                    window_geometry = self.geometry()
                    new_x = int(original_geometry.x() * width_ratio)
                    new_width = int(original_geometry.width() * width_ratio)
                else:
                    new_x = original_geometry.x()
                    new_width = original_geometry.width()
                    
                if height_ratio != 1:
                    window_geometry = self.geometry()
                    new_y = int(original_geometry.y() * height_ratio)
                    new_height = int(original_geometry.height() * height_ratio)
                else:
                    new_y = original_geometry.y()
                    new_height = original_geometry.height()
                
                widget.setGeometry(new_x, new_y, new_width, new_height)
                widget.updateGeometry()
            
                
                new_font_size = max(int(original_font_size * (width_ratio + height_ratio)/2), 8)  # Use a minimum font size of 8
                font = widget.font()
                font.setPointSize(new_font_size)
                widget.setFont(font)
                
                if isinstance(widget, QPushButton):
                    icon = widget.icon()
                    if not icon.isNull():
                        if widget.text() == "": base = 60
                        else: base = 16
                        new_icon_size = int(base * (width_ratio + height_ratio) / 2)  # Adjust the base icon size (e.g., 24)
                        widget.setIconSize(QSize(new_icon_size, new_icon_size))
        
        try:
            if scroll != None:
                for button in scroll.widget().findChildren(FileButton):
                    for i in range(button.layout().count()):
                        label = button.layout().itemAt(i)
                        label = label.widget()
                        if isinstance(label, QLabel):
                            font = label.font()
                            font.setPointSize(max(int(9 * (width_ratio + height_ratio)/2), 8))
                            label.setFont(font)
                    button.setMinimumHeight(int(30*height_ratio))
                scroll_size = [int(850*width_ratio), int(340*height_ratio)]
                scroll.setFixedSize(scroll_size[0], scroll_size[1])
        except: pass
        self.update() 
    

    
    
    def main_page(self):
        try:
            temp = window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/main.ui"
            update_ui_size(ui_path, window_geometry.width(), window_geometry.height())
            uic.loadUi(ui_path, self)
            
            self.save_sizes()
            
            self.signup_button.clicked.connect(self.signup_page)
            self.signup_button.setIcon(QIcon(assets_path+"\\new_account.svg"))

            self.login_button.clicked.connect(self.login_page)
            self.login_button.setIcon(QIcon(assets_path+"\\login.svg"))

            self.exit_button.clicked.connect(exit_program)
            self.exit_button.setIcon(QIcon(assets_path+"\\exit.svg"))
            self.setGeometry(temp)
            self.resize(window_geometry.width() + 1, window_geometry.height() + 1)
            self.resize(window_geometry.width() - 1, window_geometry.height() - 1)
        except:
            print(traceback.format_exc())

    def signup_page(self):
        try:
            temp = window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/signup.ui"
            update_ui_size(ui_path, window_geometry.width(), window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

            self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))
            self.confirm_password_toggle.clicked.connect(lambda: self.toggle_password(self.confirm_password))

            self.signup_button.clicked.connect(lambda: signup(self.email.text(), self.username.text(), self.password.text(), self.confirm_password.text()))
            self.signup_button.setShortcut("Return")
            self.signup_button.setIcon(QIcon(assets_path+"\\new_account.svg"))

            self.login_button.clicked.connect(self.login_page)
            self.login_button.setStyleSheet("background-color:transparent;color:royalblue;text-decoration: underline;border:none;")

            self.back_button.clicked.connect(self.main_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
            
            self.setGeometry(temp)
            self.resize(window_geometry.width() + 1, window_geometry.height() + 1)
            self.resize(window_geometry.width() - 1, window_geometry.height() - 1)
        except:
            print(traceback.format_exc())

    def login_page(self):
        try:
            temp = window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/login.ui"
            update_ui_size(ui_path, window_geometry.width(), window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))

            self.forgot_password_button.clicked.connect(self.forgot_password)
            self.forgot_password_button.setStyleSheet("background-color:transparent;color:royalblue;text-decoration: underline;border:none;")

            self.signup_button.clicked.connect(self.signup_page)
            self.signup_button.setStyleSheet("background-color:transparent;color:royalblue;text-decoration: underline;border:none;")

            self.login_button.clicked.connect(lambda: login(self.user.text(), self.password.text(), self.remember.isChecked()))
            self.login_button.setShortcut("Return")
            self.login_button.setIcon(QIcon(assets_path+"\\login.svg"))

            self.back_button.clicked.connect(self.main_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
            
            self.setGeometry(temp)
            self.resize(window_geometry.width() + 1, window_geometry.height() + 1)
            self.resize(window_geometry.width() - 1, window_geometry.height() - 1)
        except:
            print(traceback.format_exc())

    def forgot_password(self):
        try:
            temp = window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/forgot_password.ui"
            update_ui_size(ui_path, window_geometry.width(), window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            
            self.send_code_button.clicked.connect(lambda: reset_password(self.email.text()))
            self.send_code_button.setShortcut("Return")
            self.send_code_button.setIcon(QIcon(assets_path+"\\send.svg"))

            self.back_button.clicked.connect(self.login_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
            
            self.setGeometry(temp)
            self.resize(window_geometry.width() + 1, window_geometry.height() + 1)
            self.resize(window_geometry.width() - 1, window_geometry.height() - 1)
        except:
            print(traceback.format_exc())

    def verification_page(self, email):
        try:
            temp = window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/verification.ui"
            update_ui_size(ui_path, window_geometry.width(), window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            
            self.verify_button.clicked.connect(lambda: verify(email, self.code.text()))
            self.verify_button.setShortcut("Return")
            self.verify_button.setIcon(QIcon(assets_path+"\\verify.svg"))

            self.send_again_button.clicked.connect(lambda: send_verification(email))
            self.send_again_button.setIcon(QIcon(assets_path+"\\again.svg"))

            self.back_button.clicked.connect(self.main_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
            
            self.setGeometry(temp)
            self.resize(window_geometry.width() + 1, window_geometry.height() + 1)
            self.resize(window_geometry.width() - 1, window_geometry.height() - 1)
        except:
            print(traceback.format_exc())

    def send_verification_page(self):
        try:
            temp = window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/send_verification.ui"
            update_ui_size(ui_path, window_geometry.width(), window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            
            self.send_code_button.clicked.connect(lambda: send_verification(self.email.text()))
            self.send_code_button.setShortcut("Return")
            self.send_code_button.setIcon(QIcon(assets_path+"\\send.svg"))

            self.back_button.clicked.connect(self.main_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
            
            self.setGeometry(temp)
            self.resize(window_geometry.width() + 1, window_geometry.height() + 1)
            self.resize(window_geometry.width() - 1, window_geometry.height() - 1)
        except:
            print(traceback.format_exc())
    
    def user_page(self):
        global files, directories
        files = None
        directories = None
        if user["cwd"] == "" and deleted:
            get_deleted_files(search_filter)
            get_deleted_directories(search_filter)
        elif user["cwd"] == "" and share: 
            get_cwd_shared_files(search_filter)
            get_cwd_shared_directories(search_filter)
        else:
            get_cwd_files(search_filter)
            get_cwd_directories(search_filter)

    def run_user_page(self):
        global files, directories
        try:
            get_used_storage()
            temp = window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/account_managment.ui"
            update_ui_size(ui_path, window_geometry.width(), window_geometry.height())
            uic.loadUi(ui_path, self)
            ui_path = f"{os.getcwd()}/gui/ui/user.ui"
            update_ui_size(ui_path, window_geometry.width(), window_geometry.height())
            uic.loadUi(ui_path, self)
            
            if share or deleted: 
                self.setAcceptDrops(False)
            else: 
                self.setAcceptDrops(True)
            if share:
                self.sort.addItem(" Owner")
            self.set_cwd()
        
            if sort == "Name" or not share and sort == "Owner":
                self.sort.setCurrentIndex(0)
                files = sorted(files, key=lambda x: x.split("~")[0].lower())
                directories = sorted(directories, key=lambda x: x.split("~")[0].lower())
            elif sort == "Date":
                self.sort.setCurrentIndex(1)
                files = sorted(files, key=lambda x: str_to_date(x.split("~")[1]), reverse=True)
                directories = sorted(directories, key=lambda x: str_to_date(x.split("~")[2]), reverse=True)
            elif sort == "Type":
                self.sort.setCurrentIndex(2)
                files = sorted(files, key=lambda x: x.split("~")[0].split(".")[-1].lower())
            elif sort == "Size":
                self.sort.setCurrentIndex(3)
                files = sorted(files, key=lambda x: int(x.split("~")[2]), reverse=True)
                directories = sorted(directories, key=lambda x: int(x.split("~")[3]), reverse=True)
            elif share and sort == "Owner":
                self.sort.setCurrentIndex(4)
                files = sorted(files, key=lambda x: x.split("~")[4].lower())
                directories = sorted(directories, key=lambda x: x.split("~")[4].lower())
                
            
            self.save_sizes()
            self.draw_cwd(files, directories)
            
            self.file_upload_progress.hide()
            self.total_files.setText(f"{len(files) + len(directories)} items")
            
            self.main_text.setText(f"Welcome {user["username"]}")

            self.storage_label.setText(f"Storage used ({format_file_size(used_storage*1_000_000)} / {Limits(user["subscription_level"]).max_storage//1000} GB):")
            self.storage_remaining.setMaximum(Limits(user["subscription_level"]).max_storage)
            self.storage_remaining.setValue(int(used_storage))

            self.search.setIcon(QIcon(assets_path+"\\search.svg"))
            self.search.setText(f" Search Filter: {search_filter}")
            self.search.clicked.connect(search)
            self.search.setStyleSheet("background-color:transparent;border:none;")
            
            self.shared_button.clicked.connect(change_share)
            self.shared_button.setIcon(QIcon(assets_path+"\\share.svg"))
            
            self.recently_deleted_button.clicked.connect(change_deleted)
            self.recently_deleted_button.setIcon(QIcon(assets_path+"\\delete.svg"))
            
            self.sort.currentIndexChanged.connect(lambda: change_sort(self.sort.currentText()[1:]))
        
            
            self.user_button.clicked.connect(lambda: self.manage_account())
            self.logout_button.clicked.connect(logout)
            self.logout_button.setIcon(QIcon(assets_path+"\\logout.svg"))
            self.upload_button.setIcon(QIcon(assets_path+"\\upload.svg"))
            
            if deleted:
                try: self.upload_button.setIcon((QIcon(user_icon)))
                except: pass
                self.upload_button.setText(" Your files")
                self.upload_button.clicked.connect(change_deleted)
                self.recently_deleted_button.hide()
                self.shared_button.hide()
            
            elif share:
                try: self.upload_button.setIcon((QIcon(user_icon)))
                except: pass
                self.upload_button.setText(" Your files")
                self.upload_button.clicked.connect(change_share)
                self.shared_button.hide()
                self.recently_deleted_button.hide()
            
            else:
                self.upload_button.clicked.connect(lambda: self.file_dialog())
            
            self.user_button.setIconSize(QSize(self.user_button.size().width(), self.user_button.size().height()))
            self.user_button.setStyleSheet("padding:0px;border-radius:5px;border:none;background-color:transparent")
            
            try:
                self.user_button.setIcon((QIcon(user_icon)))
            except:
                pass
            
            self.stop_button.hide()
            self.stop_button.clicked.connect(self.stop_upload)
            self.stop_button.setIcon(QIcon(assets_path+"\\stop.svg"))
            
            self.setGeometry(temp)
            self.resize(window_geometry.width() + 1, window_geometry.height() + 1)
            self.resize(window_geometry.width() - 1, window_geometry.height() - 1)
            
            
        except:
            print(traceback.format_exc())

    def draw_cwd(self, files, directories):
        try:
            global scroll
            central_widget = self.centralWidget()
            outer_layout = QVBoxLayout()
            outer_layout.addStretch(1)
            scroll = QScrollArea()
            
            scroll.setWidgetResizable(True)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            scroll.verticalScrollBar().valueChanged.connect(self.scroll_changed)
            scroll_container_widget = QWidget()
            scroll_layout = QGridLayout()
            scroll_layout.setSpacing(5)
            if deleted: button = FileButton(["File Name", "Deleted In", "Size"])
            elif share: button = FileButton(["File Name", "Last Change", "Size", "Owner"])
            else: button = FileButton(["File Name", "Last Change", "Size"])
                
            button.setStyleSheet(f"background-color:#001122;border-radius: 3px;border:1px solid darkgrey;border-radius: 3px;")
            scroll_layout.addWidget(button)

            for i, file in enumerate(files):
                file = file.split("~")
                file_name = file[0]
                date = file[1][:-7]
                size = format_file_size(int(file[2]))
                file_id = file[3]
                perms = file[5:]
                if share:
                    button = FileButton(f" {file_name} | {date} | {size} | {file[4]}".split("|"), file_id, shared_by=file[4], perms=perms)
                else:
                    button = FileButton(f" {file_name} | {date} | {size}".split("|"), file_id)
                button.clicked.connect(lambda checked, name=file_name, id = file_id: view_file(id, name))
                scroll_layout.addWidget(button)

            for index, directory in enumerate(directories):
                directory = directory.split("~")
                size = format_file_size(int(directory[3]))
                last_change = directory[2][:-7]
                perms = directory[5:]
                if share:
                    button = FileButton(f" {directory[0]} | {last_change} | {size} | {directory[4]}".split("|"), directory[1], is_folder=True, shared_by=directory[2], perms=perms)
                else:
                    button = FileButton(f" {directory[0]} | {last_change} | {size}".split("|"), directory[1], is_folder=True)
                button.clicked.connect(lambda checked, id=directory[1]: move_dir(id))
                scroll_layout.addWidget(button)

            if (directories == [] and files == []):
                button = FileButton(["No files or folders in this directory"])
                button.setStyleSheet(f"background-color:red;border-radius: 3px;border:1px solid darkgrey;")
                scroll_layout.addWidget(button)

            if (user["cwd"] != ""):
                button = FileButton(["Back"])
                button.clicked.connect(lambda: move_dir(user["parent_cwd"]))
                scroll_layout.addWidget(button)
            
            scroll_container_widget.setLayout(scroll_layout)

            scroll.setWidget(scroll_container_widget)
            scroll.setFixedSize(850, 340)
            spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            outer_layout.addItem(spacer)
            center_layout = QHBoxLayout()
            center_layout.addStretch(1)  # Add stretchable space on the left
            scroll.verticalScrollBar().setValue(self.scroll_progress)
            center_layout.addWidget(scroll)  # Add the scroll area
            center_layout.addStretch(1)  # Add stretchable space on the right

            # Add the centered scroll area layout to the outer layout
            outer_layout.addLayout(center_layout)
            outer_layout.addStretch(1)
            central_widget.setLayout(outer_layout)
        except:
            print(traceback.format_exc())
    
    def scroll_changed(self, value):
        self.scroll_progress = value

    def manage_account(self):
        try:
            global window_geometry
            temp = window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/account_managment.ui"
            update_ui_size(ui_path, window_geometry.width(), window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()

            self.forgot_password_button.clicked.connect(lambda: reset_password(user["email"]))
            self.forgot_password_button.setIcon(QIcon(assets_path + "\\key.svg"))

            self.delete_account_button.clicked.connect(lambda: delete_user(user["email"]))
            self.delete_account_button.setIcon(QIcon(assets_path + "\\delete.svg"))

            self.upload_icon_button.clicked.connect(lambda: upload_icon())
            self.upload_icon_button.setIcon(QIcon(assets_path + "\\profile.svg"))

            self.subscriptions_button.clicked.connect(self.subscriptions_page)
            self.subscriptions_button.setIcon(QIcon(assets_path + "\\upgrade.svg"))

            self.change_username_button.clicked.connect(change_username)
            self.change_username_button.setIcon(QIcon(assets_path + "\\change_user.svg"))

            self.back_button.clicked.connect(self.user_page)
            self.back_button.setIcon(QIcon(assets_path + "\\back.svg"))
            
            self.setGeometry(temp)
            self.resize(window_geometry.width() + 1, window_geometry.height() + 1)
            self.resize(window_geometry.width() - 1, window_geometry.height() - 1)
        except:
            print(traceback.format_exc())

    def subscriptions_page(self):
        try:
            temp = window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/subscription.ui"
            update_ui_size(ui_path, window_geometry.width(), window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
                
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
                self.professional_button.setStyleSheet("background-color:dimgrey")

            self.storage_remaining.setMaximum(Limits(user["subscription_level"]).max_storage)
            self.storage_remaining.setValue(int(used_storage))
            self.storage_label.setText(f"Storage used ({format_file_size(used_storage*1_000_000)} / {Limits(user["subscription_level"]).max_storage//1000} GB):")
            
            self.setGeometry(temp)
            self.resize(window_geometry.width() + 1, window_geometry.height() + 1)
            self.resize(window_geometry.width() - 1, window_geometry.height() - 1)
        except:
            print(traceback.format_exc())

    def recovery(self, email):
        try:
            temp = window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/recovery.ui"
            update_ui_size(ui_path, window_geometry.width(), window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
                
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

            self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))
            self.confirm_password_toggle.clicked.connect(lambda: self.toggle_password(self.confirm_password))

            self.reset_button.clicked.connect(lambda: password_recovery(email, self.code.text(), self.password.text(), self.confirm_password.text()))
            self.reset_button.setShortcut("Return")
            self.reset_button.setIcon(QIcon(assets_path+"\\reset.svg"))

            self.send_again_button.clicked.connect(lambda: reset_password(email))
            self.send_again_button.setIcon(QIcon(assets_path+"\\again.svg"))

            self.back_button.clicked.connect(self.manage_account)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
            
            self.setGeometry(temp)
            self.resize(window_geometry.width() + 1, window_geometry.height() + 1)
            self.resize(window_geometry.width() - 1, window_geometry.height() - 1)
        except:
            print(traceback.format_exc())
        
    def not_connected_page(self):
        try:
            temp = window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/not_connected.ui"
            update_ui_size(ui_path, window_geometry.width(), window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            
            self.ip.setText(ip)
            self.port.setText(str(port))
            
            self.connect_button.clicked.connect(lambda: connect_server(self.ip.text(), self.port.text()))
            self.connect_button.setShortcut("Return")
            self.connect_button.setIcon(QIcon(assets_path+"\\connect.svg"))
            
            self.exit_button.clicked.connect(force_exit)
            self.exit_button.setIcon(QIcon(assets_path+"\\exit.svg"))
            
            self.setGeometry(temp)
            self.resize(window_geometry.width() + 1, window_geometry.height() + 1)
            self.resize(window_geometry.width() - 1, window_geometry.height() - 1)

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
                file_queue.extend(file_paths)  # Add dropped files to the queue
                send_files()
                    
        except:
            print(traceback.format_exc())
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():  # Check if the dragged object is a file (URL)
            event.acceptProposedAction()  # Accept the drag event

    # This function handles when the dragged object is dropped
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
            file_queue.extend(file_paths)  # Add dropped files to the queue
            send_files()

    
    def set_error_message(self, msg):
        try:
            if (hasattr(self, "message")):
                self.message.setStyleSheet("color: red;")
                self.message.setText(msg)
        except Exception:
            pass

    def set_message(self, msg):
        if (hasattr(self, "message")):
            self.message.setStyleSheet("color: lightgreen;")
            self.message.setText(msg)

    def set_cwd(self):
        if (hasattr(self, "cwd")):
            self.cwd.setStyleSheet("color: yellow;")
            if share: self.cwd.setText(f"Shared > {" > ".join(user['cwd_name'].split("\\"))}"[:-3])
            elif deleted: self.cwd.setText(f"Deleted > {" > ".join(user['cwd_name'].split("\\"))}"[:-3])
            else: self.cwd.setText(f"{user['username']} > {" > ".join(user['cwd_name'].split("\\"))}"[:-3])
    
    def stop_upload(self):
        self.stop_button.setEnabled(False)
        send_data(b"STOP")





# Files functions
class FileSenderThread(QThread):
    finished = pyqtSignal()  # Signal to notify that file sending is done
    error = pyqtSignal(str)  # Signal to notify error messages
    progress = pyqtSignal(int)  # Signal to update progress bar
    progress_reset = pyqtSignal(int)
    message = pyqtSignal(str)  # Signal to update the message

    def __init__(self, cmd, file_id):
        super().__init__()
        self.files_uploaded = []
        self.cmd = cmd
        self.file_id = file_id

    def run(self):
        for file_path in file_queue:
            try: window.stop_button.setEnabled(True)
            except: pass
            if self.file_id != None:
                file_name = self.file_id
            else:
                file_name = file_path.split("/")[-1]  # Extract the file name
            file_id = uuid.uuid4().hex
            start_string = f"{self.cmd}|{file_name}|{user["cwd"]}|{os.path.getsize(file_path)}|{file_id}"
            send_data(start_string.encode())
            if not os.path.isfile(file_path):
                self.error.emit("File path was not found")
                return

            size = os.path.getsize(file_path)
            left = size % chunk_size
            sent = 0
            self.progress.emit(0)
            self.progress_reset.emit(size)
            self.message.emit(f"{file_name} is being uploaded")
            try:
                with open(file_path, 'rb') as f:
                    for i in range(size // chunk_size):
                        location_infile = f.tell()
                        data = f.read(chunk_size)
                        send_data(f"FILD|{file_id}|{location_infile}|".encode() + data)
                        sent += chunk_size
                        self.progress_reset.emit(size)
                        self.progress.emit(sent)  # Update progress bar
                    
                    location_infile = f.tell()
                    data = f.read(left)
                    if data != b"":
                        send_data(f"FILE|{file_id}|{location_infile}|".encode() + data)
                        self.progress_reset.emit(size)
                        self.progress.emit(sent)  # Final progress update
            except:
                print(traceback.format_exc())
                return
        if self.file_id != None: os.remove(file_path.split("/")[-1])
        self.finished.emit() 
            


def send_files(cmd = "FILS", file_id = None):
    try: window.file_upload_progress.show()
    except: pass
    try:
        window.stop_button.setEnabled(True)
        window.stop_button.show()
    except: pass
    thread = FileSenderThread(cmd, file_id)

    active_threads.append(thread)


    thread.finished.connect(thread.deleteLater)
    thread.finished.connect(lambda: active_threads.remove(thread))
    
    thread.progress.connect(update_progress)
    thread.progress_reset.connect(reset_progress)# Connect progress signal to progress bar
    thread.message.connect(window.set_message)
    thread.error.connect(window.set_error_message)
    
    thread.start()

def update_progress(value):
    try: window.file_upload_progress.setValue(value)
    except: pass

def reset_progress(value):
    try: window.file_upload_progress.setMaximum(value)
    except: pass


                
class FileSaverThread(QThread):
    finished = pyqtSignal()  # Signal to notify that file sending is done
    error = pyqtSignal(str)  # Signal to notify error messages
    progress = pyqtSignal(int)  # Signal to update progress bar
    progress_reset = pyqtSignal(int)
    message = pyqtSignal(str)  # Signal to update the message

    def __init__(self, save_loc, file_name, size):
        super().__init__()
        self.save_loc = save_loc
        self.file_name = file_name
        self.size = size

    def run(self):
        try:
            if not os.path.exists(os.path.dirname(self.save_loc)):
                os.makedirs(os.path.dirname(self.save_loc))
            data = b''
            self.progress.emit(0)
            self.progress_reset.emit(self.size)# Initialize progress bar to 0
            self.message.emit(f"{self.file_name} is being downloaded")
            total = 0
            with open(self.save_loc, 'wb') as f:
                while True:
                    data = recv_data()
                    if not data:
                        raise Exception
                    total += len(data)
                    self.progress.emit(total)
                    if (data[:4] == b"RILD"):
                        f.write(data[4:])
                    elif (data[:4] == b"RILE"):
                        f.write(data[4:])
                        break
                    else:
                        try:
                            # Parse the reply and split it according to the protocol separator
                            reply = reply.decode()
                            fields = reply.split("|")
                            code = fields[0]
                            if code == 'ERRR':   # If server returned error show to user the error
                                self.error.emit(fields[2])
                            elif code == 'DOWR':
                                to_show = f'File {fields[1]} was downloaded'
                                self.message.emit(to_show)  # Send message via signal
                            break
                        except:
                            print(traceback.format_exc())
                            break
                    data = b''
                reply = recv_data()
                reply = reply.decode()
                fields = reply.split("|")
                code = fields[0]
                            
                if code == 'ERRR':   # If server returned error show to user the error
                    self.error.emit(fields[2])
                elif code == 'DOWR':
                    to_show = f'File {fields[1]} was downloaded'
                    self.message.emit(to_show)  # Send message via signal
        except:
            print(traceback.format_exc())
        self.finished.emit() 
            





def view_file(file_id, file_name):
    send_data(b"VIEW|" + file_id.encode())
    save_path = f"{os.getcwd()}\\temp-{file_name}"
    files_downloading[file_id] = File(save_path, file_id, 0, True)

    
def activate_file_view(file_id):
    save_path = files_downloading[file_id].save_location
    file_viewer_dialog("File Viewer", save_path)

    save = show_confirmation_dialog("Do you want to save changes?")
    if save:
        file_queue.extend([save_path])  # Add dropped files to the queue
        send_files("UPFL", file_id)
    else: 
        os.remove(save_path)

def end_view(file_id):
    send_data(b"VIEE|" + file_id.encode())

def change_share():
    global share
    share = not share
    move_dir("")

def change_deleted():
    global deleted
    deleted = not deleted
    move_dir("")

def change_sort(new_sort):
    global sort
    sort = new_sort
    window.run_user_page()

def move_dir(new_dir):
    send_data(f"MOVD|{new_dir}".encode())


def get_user_icon():
    send_data(b"GICO")
    files_downloading["user"] = File(user_icon, "user", 0)


def get_used_storage():
    send_data(b"GEUS")


def upload_icon():
    try:
        file_path, _ = QFileDialog.getOpenFileName(window, "Open File", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.ico);")
        if file_path:
            file_queue.extend([file_path])
            send_files("ICOS")
    except:
        print(traceback.format_exc())



def change_username():
    name = user["username"]
    new_name = new_name_dialog("Change Username", "Enter new  username:", name)
    if new_name is not None and new_name != name:
        send_data(b"CHUN|" + new_name.encode())


def subscribe(level):
    send_data(b"SUBL|" + str(level).encode())


def share_file(file_id, user_cred, read = "False", write = "False", delete = "False", rename = "False", download = "False", share = "False"):
    app = QApplication.instance()  # Use existing QApplication
    if app is None:
        app = QApplication([])  # Create a new instance if it doesn't exist

    dialog = QDialog()
    dialog.setWindowTitle("File Share Options")
    dialog.setStyleSheet("font-size:15px;")
    dialog.resize(600, 400)

    # Group the checkboxes for better organization
    permissions_group = QGroupBox("Permissions")
    permissions_layout = QGridLayout()

    read_cb = QCheckBox("Read")
    read_cb.setChecked(read == "True")
    permissions_layout.addWidget(read_cb, 0, 0)  # Row 0, Column 0

    write_cb = QCheckBox("Write")
    write_cb.setChecked(write == "True")
    permissions_layout.addWidget(write_cb, 0, 1)  # Row 0, Column 1

    delete_cb = QCheckBox("Delete")
    delete_cb.setChecked(delete == "True")
    permissions_layout.addWidget(delete_cb, 1, 0)  # Row 1, Column 0

    rename_cb = QCheckBox("Rename")
    rename_cb.setChecked(rename == "True")
    permissions_layout.addWidget(rename_cb, 1, 1)  # Row 1, Column 1

    download_cb = QCheckBox("Download")
    download_cb.setChecked(download == "True")
    permissions_layout.addWidget(download_cb, 2, 0)  # Row 2, Column 0

    share_cb = QCheckBox("Share")
    share_cb.setChecked(share == "True")
    permissions_layout.addWidget(share_cb, 2, 1)  # Row 2, Column 1

    # Set the layout for the permissions group
    permissions_group.setLayout(permissions_layout)

    # Submit button with a spacer for better positioning
    submit_btn = QPushButton("Submit")
    submit_btn.setShortcut("Return")
    submit_btn.clicked.connect(lambda: send_share_premissions(
        dialog, file_id, user_cred, 
        read_cb.isChecked(), write_cb.isChecked(), delete_cb.isChecked(),
        rename_cb.isChecked(), download_cb.isChecked(), share_cb.isChecked()
    ))

    # Adding a spacer to push the button to the bottom
    button_layout = QHBoxLayout()
    button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
    button_layout.addWidget(submit_btn)

    # Main layout
    main_layout = QVBoxLayout()
    main_layout.addWidget(permissions_group)
    main_layout.addLayout(button_layout)

    dialog.setLayout(main_layout)
    dialog.exec()

def send_share_premissions(dialog, file_id, user_cred, read, write, delete, rename, download, share):
    dialog.accept()
    to_send = f"SHRP|{file_id}|{user_cred}|{read}|{write}|{delete}|{rename}|{download}|{share}"
    send_data(to_send.encode())

# Begin server requests related functions


def login(cred, password, remember_temp):
    """
    Send login request to server
    """
    global remember
    remember = remember_temp
    items = [cred, password]
    send_string = build_req_string("LOGN", items)
    send_data(send_string)
    


def logout():
    """
    Send logout request to server
    """
    global logged_in_user
    logged_in_user = {}
    send_string = build_req_string("LOGU")
    send_data(send_string)


def signup(email, username, password, confirm_password):
    """
    Send signup request to server
    """
    items = [email, username, password, confirm_password]

    send_string = build_req_string("SIGU", items)
    send_data(send_string)


def reset_password(email):
    """
    Send password reset request to server
    """
    items = [email]
    send_string = build_req_string("FOPS", items)
    send_data(send_string)


def password_recovery(email, code, new_password, confirm_new_password):
    """
    Send password recovery code and new password to server
    """
    items = [email, code, new_password, confirm_new_password]
    send_string = build_req_string("PASR", items)
    send_data(send_string)


def send_verification(email):
    """
    Send verification request to server
    """
    items = [email]
    send_string = build_req_string("SVER", items)
    send_data(send_string)


def verify(email, code):
    """
    Send verification code to server for confirmation
    """
    items = [email, code]
    send_string = build_req_string("VERC", items)
    send_data(send_string)



def delete_user(email):
    """
    Send delete user request to server
    """
    if (confirm_account_deletion(email)):
        items = [email]
        send_string = build_req_string("DELU", items)
        send_data(send_string)


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

def force_exit():
    sys.exit()


def get_files(type, filter):
    global file, directories
    get_types = {1: [b"GETP", b"PATH"], 2: [b"GESP", b"PASH"], 3: [b"GEDP", b"PADH"], 4: [b"GETD", b"PATD"], 5: [b"GESD", b"PASD"], 6: [b"GEDD", b"PADD"]}
    to_send = get_types[type][0] + b"|" + user["cwd"].encode()
    if filter:
        to_send += b"|" + filter.encode()

    send_data(to_send)


def get_cwd_files(filter=None):
    return get_files(1, filter)

def get_cwd_shared_files(filter=None):
    return get_files(2, filter)

def get_deleted_files(filter=None):
    return get_files(3, filter)


def get_cwd_directories(filter=None):
    return get_files(4, filter)

def get_cwd_shared_directories(filter=None):
    return get_files(5, filter)

def get_deleted_directories(filter=None):
    return get_files(6, filter)

def save_cookie(cookie):
    if not os.path.exists(os.getcwd() + "\\cookies"):
        os.makedirs(os.getcwd() + "\\cookies")
    with open(cookie_path, "w") as f:
        f.write(cookie)

def send_cookie():
    try:
        with open(cookie_path, "r") as f:
            cookie = f.read()
            send_data(b"COKE|" + cookie.encode())
    except:
        print(traceback.format_exc())
        pass
    
    


# Begin server replies handling functions

def protocol_parse_reply(reply):
    """
    Server reply parsing and handeling
    Checking error codes and respective answers to user
    Performing action according to response from server
    """
    global files, directories, last_msg, last_error_msg
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
            if remember:
                send_data(b"GENC")

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
            global share, deleted
            user["email"] = "guest"
            user["username"] = "guest"
            user["subscription_level"] = 0
            user["cwd"] = ""
            user["parent_cwd"] = ""
            user["cwd_name"] = ""
            share = False
            deleted = False
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
        
        elif code == 'FISS':
            to_show = f'File {fields[1]} started uploading'

            window.user_page()
            window.set_message(to_show)

        elif code == 'MOVR':
            user["cwd"] = fields[1]
            user["parent_cwd"] = fields[2]
            user["cwd_name"] = fields[3]
            to_show = f'Succesfully moved to {fields[3]}'
            window.user_page()
            
        elif code == "RILD" or code == "RILE":
            file_id = fields[1].decode()
            location_infile = int(fields[2].decode())
            data = reply[4 + len(file_id) + len(str(location_infile)) + 3:]
            if file_id in files_downloading.keys():
                file = files_downloading[file_id]
                file.add_data(data, location_infile)
            
            if code == "RILE":
                if file_id in files_downloading.keys():
                    if files_downloading[file_id].is_view:
                        end_view(file_id)
                        activate_file_view(file_id)
                    del files_downloading[file_id]
                try: window.stop_button.setEnabled(False)
                except: pass
                window.stop_button.hide()
            to_show = "File data recieved"
            

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
        elif code == "RECR":
            name = fields[1]
            to_show = f"Succefully recovered {name}"
            window.user_page()
            window.set_message(to_show)
        elif code == "UPFR":
            name = fields[1]
            to_show = f"Succefully saved changes to file {name}"
            window.user_page()
            window.set_message(to_show)
        elif code == "VIRR":
            to_show = "File viewing released"
        elif code == "STOR":
            name = fields[1]
            to_show = f"Upload of {name} stopped"
            window.set_message(to_show)
        elif code == "PATH" or code == "PASH" or code == "PADH":
            files = fields[1:]
            if files != None and directories != None:
                window.run_user_page()
            to_show = "Got files"
        elif code == "PATD" or code == "PASD" or code == "PADD":
            directories = fields[1:]
            if files != None and directories != None:
                window.run_user_page()
            to_show = "Got directories"
        else:
            window.set_message("Unknown command " + code)
            
    except Exception as e:   # Error
        print(traceback.format_exc())
    return to_show


def handle_reply(reply):
    """
    Getting server reply and parsing it
    If some error occured or no response disconnect
    """
    try:
        logtcp('recv', reply)

        to_show = protocol_parse_reply(reply)
        print(to_show)
        if to_show == "Invalid reply from server":
            print(to_show)
        
        # If exit request succeded, dissconnect
        if to_show == "Server acknowledged the exit message":
            print('Succefully exit')
            sock.close()
            sys.exit()
        elif to_show == None:
            sock.close()
            window.not_connected_page()
            window.set_error_message("Lost connection to server")
    except socket.error as err:   # General error handling
        print(traceback.format_exc())
        return
    except Exception as err:
        print(traceback.format_exc())
        return

class ReceiveThread(QThread):
    # Define a signal to emit data received from receive_replies
    reply_received = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()
        self.running = True  # Add a flag to control the thread loop

    def run(self):
         while self.running:
            # Call your receive_replies logic here
            reply = recv_data()  # Assume this method exists and returns a string
            if reply:
                self.reply_received.emit(reply)  # Emit the received reply to the main thread

# Main function and start of code
def connect_server(new_ip, new_port):
    global sock, ip, port
    window.set_message(f"Trying to connect to {new_ip} {new_port}...")
    QApplication.processEvents()
    try:
        ip = new_ip
        port = int(new_port)
        sock = socket.socket()
        sock.connect((ip, int(port)))
        set_sock(sock)
        shared_secret = rsa_exchange(sock) 
        if not shared_secret:
            sock.close()
            return
        set_secret(shared_secret)
        window.main_page()
        send_cookie()
        if user["username"] != "guest":
            window.set_message(f'Connect succeeded {ip} {port}')
        return sock
    except:
        window.not_connected_page()
        window.set_error_message(f'Server was not found {ip} {port}')
        return None

def main():
    """
    Main function
    Create tkinter root and start secure connection to server
    Connect to server via addr param
    """
    global sock, window, app
    try:
        app = QtWidgets.QApplication(sys.argv)
        try: 
            with open(f"{os.getcwd()}/gui/css/style.css", 'r') as f: app.setStyleSheet(f.read())
        except: pass
        window = MainWindow()
        window.show()
        window.not_connected_page()
        sock = connect_server(ip, port)
        receive_thread = ReceiveThread()
        receive_thread.start()
        receive_thread.reply_received.connect(handle_reply)
        sys.exit(app.exec())
    except Exception as e:
        print(traceback.format_exc())


if __name__ == "__main__":   # Run main
    #sys.stdout = Logger()
    if len(sys.argv) >= 2: ip = sys.argv[1]
    if len(sys.argv) >= 3: port = sys.argv[2]

    main()

