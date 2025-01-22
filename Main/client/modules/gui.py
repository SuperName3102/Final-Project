# 2024 © Idan Hazay
# Import libraries

from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QWidget,QLabel, QVBoxLayout, QPushButton, QCheckBox, QGroupBox, QFileDialog, QLineEdit, QGridLayout, QScrollArea, QHBoxLayout, QSpacerItem, QSizePolicy, QMenu
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QMoveEvent, QResizeEvent, QContextMenuEvent
from PyQt6.QtCore import QSize

import os, time

from modules.config import *
from modules.file_viewer import *
from modules.limits import Limits

from modules import helper, protocol, file_send, dialogs

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app, network):
        super().__init__()
        self.app = app
        self.window_geometry = window_geometry
        self.save_sizes()
        self.setGeometry(self.window_geometry)
        self.original_width = self.width()
        self.original_height = self.height()
        self.scroll_progress = 0
        s_width = app.primaryScreen().geometry().width()
        s_height = app.primaryScreen().geometry().height()
        self.resize(s_width*3//4, s_height*2//3)
        self.move(s_width//8, s_height//6)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WidgetAttribute.WA_PaintOnScreen, True)
        self.current_files_amount = items_to_load
        self.last_load = time.time()
        self.scroll_size = scroll_size
        
        self.user = {"email": "guest", "username": "guest", "subscription_level": 0, "cwd": "", "parent_cwd": "", "cwd_name": ""}
        
        self.json = helper.JsonHandle()
        self.network = network
        self.protocol = protocol.Protocol(self.network, self)
        self.file_sending = file_send.FileSending(self)
        
        self.search_filter = None
        self.share = False
        self.deleted = False
        self.sort = "Name"
        self.sort_direction = True
        self.remember = False
        
        self.files = []
        self.directories = []
        self.files_downloading = {}
        self.currently_selected = []
        self.uploading_file_id = ""
        self.used_storage = 0
        self.items_amount = 0
        
        self.original_sizes = {}
        self.scroll = None
        
        self.start()

    def start(self):
        try: 
            with open(f"{os.getcwd()}/gui/css/style.css", 'r') as f: self.app.setStyleSheet(f.read())
        except: print(traceback.format_exc())
        if (os.path.isfile(f"{os.getcwd()}/assets/icon.ico")):
            self.setWindowIcon(QIcon(f"{os.getcwd()}/assets/icon.ico"))
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete and len(self.currently_selected) > 0:
            self.delete()
        elif event.key() == Qt.Key.Key_R and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if self.user["username"] != "guest":
                self.user_page()
        elif event.key() == Qt.Key.Key_A and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if self.scroll != None:
                for button in self.scroll.widget().findChildren(FileButton):
                    if button.id != None and button not in self.currently_selected:
                        self.select_item(button)
        elif event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if self.user["username"] != "guest": self.protocol.search()
        super().keyPressEvent(event)
    
    def save_sizes(self):
        for widget in self.findChildren(QWidget):
            # Save both the original geometry and the original font size (if the widget has a font)
            font_size = widget.font().pointSize()
            self.original_sizes[widget] = {
                'geometry': widget.geometry(),
                'font_size': font_size
            }
    
    def moveEvent(self, event: QMoveEvent):
        self.window_geometry = self.geometry()
    
    def resizeEvent(self, event):
        
        new_width = self.width()
        new_height = self.height()

        # Calculate the scaling factors for width and height
        width_ratio = new_width / self.original_width
        height_ratio = new_height / self.original_height
        
        # Resize all child widgets based on the scaling factor
        
        for widget in self.findChildren(QWidget):
            if widget in self.original_sizes.keys():
                original_geometry = self.original_sizes[widget]['geometry']
                original_font_size = self.original_sizes[widget]['font_size']
                if width_ratio != 1:
                    self.window_geometry = self.geometry()
                    new_x = int(original_geometry.x() * width_ratio)
                    new_width = int(original_geometry.width() * width_ratio)
                else:
                    new_x = original_geometry.x()
                    new_width = original_geometry.width()
                    
                if height_ratio != 1:
                    self.window_geometry = self.geometry()
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
            if self.scroll != None:
                for button in self.scroll.widget().findChildren(FileButton):
                    for i in range(button.layout().count()):
                        label = button.layout().itemAt(i)
                        label = label.widget()
                        if isinstance(label, QLabel):
                            font = label.font()
                            font.setPointSize(max(int(9 * (width_ratio + height_ratio)/2), 8))
                            label.setFont(font)
                    button.setMinimumHeight(int(30*height_ratio))
                self.scroll_size = [int(850*width_ratio), int(340*height_ratio)]
                self.scroll.setFixedSize(self.scroll_size[0], self.scroll_size[1])
        except: pass

        #QApplication.restoreOverrideCursor()
        #QApplication.processEvents()
        
    def main_page(self):
        try:
            temp = self.window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/main.ui"
            helper.update_ui_size(ui_path, self.window_geometry.width(), self.window_geometry.height())
            uic.loadUi(ui_path, self)
            
            self.save_sizes()
            
            self.signup_button.clicked.connect(self.signup_page)
            self.signup_button.setIcon(QIcon(assets_path+"\\new_account.svg"))

            self.login_button.clicked.connect(self.login_page)
            self.login_button.setIcon(QIcon(assets_path+"\\login.svg"))

            self.exit_button.clicked.connect(self.protocol.exit_program)
            self.exit_button.setIcon(QIcon(assets_path+"\\exit.svg"))
            self.setGeometry(temp)
            self.force_update_window()
        except:
            print(traceback.format_exc())

    def signup_page(self):
        try:
            temp = self.window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/signup.ui"
            helper.update_ui_size(ui_path, self.window_geometry.width(), self.window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

            self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))
            self.confirm_password_toggle.clicked.connect(lambda: self.toggle_password(self.confirm_password))

            self.signup_button.clicked.connect(lambda: self.protocol.signup(self.email.text(), self.username.text(), self.password.text(), self.confirm_password.text()))
            self.signup_button.setShortcut("Return")
            self.signup_button.setIcon(QIcon(assets_path+"\\new_account.svg"))

            self.login_button.clicked.connect(self.login_page)
            self.login_button.setStyleSheet("background-color:transparent;color:royalblue;text-decoration: underline;border:none;")

            self.back_button.clicked.connect(self.main_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
            
            self.setGeometry(temp)
            self.force_update_window()
        except:
            print(traceback.format_exc())

    def login_page(self):
        try:
            temp = self.window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/login.ui"
            helper.update_ui_size(ui_path, self.window_geometry.width(), self.window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))

            self.forgot_password_button.clicked.connect(self.forgot_password)
            self.forgot_password_button.setStyleSheet("background-color:transparent;color:royalblue;text-decoration: underline;border:none;")

            self.signup_button.clicked.connect(self.signup_page)
            self.signup_button.setStyleSheet("background-color:transparent;color:royalblue;text-decoration: underline;border:none;")

            self.login_button.clicked.connect(lambda: self.protocol.login(self.credi.text(), self.password.text(), self.remember.isChecked()))
            self.login_button.setShortcut("Return")
            self.login_button.setIcon(QIcon(assets_path+"\\login.svg"))

            self.back_button.clicked.connect(self.main_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
            
            self.setGeometry(temp)
            self.force_update_window()
        except:
            print(traceback.format_exc())

    def forgot_password(self):
        try:
            temp = self.window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/forgot_password.ui"
            helper.update_ui_size(ui_path, self.window_geometry.width(), self.window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            
            self.send_code_button.clicked.connect(lambda: self.protocol.reset_password(self.email.text()))
            self.send_code_button.setShortcut("Return")
            self.send_code_button.setIcon(QIcon(assets_path+"\\send.svg"))

            self.back_button.clicked.connect(self.login_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
            
            self.setGeometry(temp)
            self.force_update_window()
        except:
            print(traceback.format_exc())

    def verification_page(self, email):
        try:
            temp = self.window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/verification.ui"
            helper.update_ui_size(ui_path, self.window_geometry.width(), self.window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            
            self.verify_button.clicked.connect(lambda: self.protocol.verify(email, self.code.text()))
            self.verify_button.setShortcut("Return")
            self.verify_button.setIcon(QIcon(assets_path+"\\verify.svg"))

            self.send_again_button.clicked.connect(lambda: self.protocol.send_verification(email))
            self.send_again_button.setIcon(QIcon(assets_path+"\\again.svg"))

            self.back_button.clicked.connect(self.main_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
            
            self.setGeometry(temp)
            self.force_update_window()
        except:
            print(traceback.format_exc())

    def send_verification_page(self):
        try:
            temp = self.window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/send_verification.ui"
            helper.update_ui_size(ui_path, self.window_geometry.width(), self.window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            
            self.send_code_button.clicked.connect(lambda: self.protocol.send_verification(self.email.text()))
            self.send_code_button.setShortcut("Return")
            self.send_code_button.setIcon(QIcon(assets_path+"\\send.svg"))

            self.back_button.clicked.connect(self.main_page)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
            
            self.setGeometry(temp)
            self.force_update_window()
        except:
            print(traceback.format_exc())
    
    def user_page(self):
        self.update_user_page()
        self.run_user_page()
        
    def update_user_page(self):
        self.files = None
        self.directories = None
        self.protocol.get_used_storage()
        if self.user["cwd"] == "" and self.deleted:
            self.protocol.get_deleted_files(self.search_filter)
            self.protocol.get_deleted_directories(self.search_filter)
        elif self.user["cwd"] == "" and self.share: 
            self.protocol.get_cwd_shared_files(self.search_filter)
            self.protocol.get_cwd_shared_directories(self.search_filter)
        else:
            self.protocol.get_cwd_files(self.search_filter)
            self.protocol.get_cwd_directories(self.search_filter)

    def run_user_page(self):
        try:
            temp = self.window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/account_managment.ui"
            helper.update_ui_size(ui_path, self.window_geometry.width(), self.window_geometry.height())
            uic.loadUi(ui_path, self)
            ui_path = f"{os.getcwd()}/gui/ui/user.ui"
            helper.update_ui_size(ui_path, self.window_geometry.width(), self.window_geometry.height())
            uic.loadUi(ui_path, self)
            
            if self.share or self.deleted: self.setAcceptDrops(False)
            else: self.setAcceptDrops(True)
            if self.share: self.sort_widget.addItem(" Owner")
            self.set_cwd()
            
            if len(self.file_sending.active_threads) == 0:
                self.file_upload_progress.hide()
                self.stop_button.hide()
            self.currently_selected = []
            
            self.main_text.setText(f"Welcome {self.user["username"]}")

            self.storage_remaining.setMaximum(Limits(self.user["subscription_level"]).max_storage)
            self.set_used_storage()
            
            self.sort_widget.currentIndexChanged.connect(lambda: self.change_sort(self.sort.currentText()[1:]))
            
            self.search_button.setIcon(QIcon(assets_path+"\\search.svg"))
            self.search_button.setText(f" Search Filter: {self.search_filter}")
            self.search_button.clicked.connect(self.protocol.search)
            self.search_button.setStyleSheet("background-color:transparent;border:none;")
            
            self.refresh.setIcon(QIcon(assets_path+"\\refresh.svg"))
            self.refresh.setText(f" ")
            self.refresh.clicked.connect(self.user_page)
            self.refresh.setStyleSheet("background-color:transparent;border:none;")
            
            self.shared_button.clicked.connect(self.protocol.change_share)
            self.shared_button.setIcon(QIcon(assets_path+"\\share.svg"))
            
            self.recently_deleted_button.clicked.connect(self.protocol.change_deleted)
            self.recently_deleted_button.setIcon(QIcon(assets_path+"\\delete.svg"))
        
            self.user_button.clicked.connect(lambda: self.manage_account())
            self.logout_button.clicked.connect(self.protocol.logout)
            self.logout_button.setIcon(QIcon(assets_path+"\\logout.svg"))
            self.upload_button.setIcon(QIcon(assets_path+"\\upload.svg"))
            
            if self.deleted:
                try: self.upload_button.setIcon((QIcon(user_icon)))
                except: pass
                self.upload_button.setText(" Your files")
                self.upload_button.clicked.connect(self.protocol.change_deleted)
                self.recently_deleted_button.hide()
                self.shared_button.hide()
            
            elif self.share:
                try: self.upload_button.setIcon((QIcon(user_icon)))
                except: pass
                self.upload_button.setText(" Your files")
                self.upload_button.clicked.connect(self.protocol.change_share)
                self.shared_button.hide()
                self.recently_deleted_button.hide()
            
            else:
                self.upload_button.clicked.connect(lambda: self.file_dialog())
            
            self.user_button.setIconSize(QSize(self.user_button.size().width(), self.user_button.size().height()))
            self.user_button.setStyleSheet("padding:0px;border-radius:5px;border:none;background-color:transparent")
            
            try: self.user_button.setIcon((QIcon(user_icon)))
            except: pass
            
            self.stop_button.clicked.connect(self.stop_upload)
            self.stop_button.setIcon(QIcon(assets_path+"\\stop.svg"))
            self.setGeometry(temp)
            self.force_update_window()
            
            
        except:
            print(traceback.format_exc())

    def draw_cwd(self):
        try:
            
            central_widget = self.centralWidget()
            
            outer_layout = QVBoxLayout()
            outer_layout.addStretch(1)
            scroll = QScrollArea()
            self.scroll = scroll
            
            scroll.setWidgetResizable(True)
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            scroll_container_widget = QWidget()
            scroll_layout = QGridLayout()
            scroll_layout.setSpacing(5)
            if self.deleted: button = FileButton(self, ["File Name", "Deleted In", "Size"])
            elif self.share: button = FileButton(self, ["File Name", "Last Change", "Size", "Owner"])
            else: button = FileButton(self, ["File Name", "Last Change", "Size"])
                
            button.setStyleSheet(f"background-color:#001122;border-radius: 3px;border:1px solid darkgrey;border-radius: 3px;")
            scroll_layout.addWidget(button)

            for file in self.files:
                file = file.split("~")
                file_name = file[0]
                date = file[1][:-7]
                size = helper.format_file_size(int(file[2]))
                file_id = file[3]
                perms = file[5:]
                if self.share:
                    button = FileButton(self, f" {file_name} | {date} | {size} | {file[4]}".split("|"), file_id, shared_by=file[4], perms=perms, size = int(file[2]), name=file_name)
                else:
                    button = FileButton(self, f" {file_name} | {date} | {size}".split("|"), file_id, size = int(file[2]), name=file_name)
                button.clicked.connect(lambda checked, btn=button: self.select_item(btn))
                scroll_layout.addWidget(button)

            for directory in self.directories:
                directory = directory.split("~")
                dir_name = directory[0]
                dir_id = directory[1]
                size = helper.format_file_size(int(directory[3]))
                last_change = directory[2][:-7]
                perms = directory[5:]
                if self.share:
                    button = FileButton(self, f" {dir_name} | {last_change} | {size} | {directory[4]}".split("|"), dir_id, is_folder=True, shared_by=directory[2], perms=perms, size = int(directory[3]), name=dir_name)
                else:
                    button = FileButton(self, f" {dir_name} | {last_change} | {size}".split("|"), dir_id, is_folder=True, size = int(directory[3]), name=dir_name)
                button.clicked.connect(lambda checked, btn=button: self.select_item(btn))
                scroll_layout.addWidget(button)

            if (self.directories == [] and self.files == []):
                button = FileButton(self, ["No files or folders in this directory"])
                button.setStyleSheet(f"background-color:red;border-radius: 3px;border:1px solid darkgrey;")
                scroll_layout.addWidget(button)

            if (self.user["cwd"] != ""):
                # Create the "Back" button
                button = FileButton(self, ["Back"])
                button.clicked.connect(lambda: self.protocol.move_dir(self.user["parent_cwd"]))
                scroll_layout.addWidget(button)
            
            scroll_container_widget.setLayout(scroll_layout)
            scroll.setWidget(scroll_container_widget)
            scroll.setFixedSize(850, 340)
            
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
    
    def scroll_changed(self, value):
        self.scroll_progress = value
        total_scroll_height = self.scroll.verticalScrollBar().maximum()
        if self.scroll_progress/total_scroll_height > 0.95 and len(self.directories) + len(self.files) < int(self.items_amount):
            self.current_files_amount += items_to_load
            self.user_page()


    def manage_account(self):
        try:
            temp = self.window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/account_managment.ui"
            helper.update_ui_size(ui_path, self.window_geometry.width(), self.window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            self.forgot_password_button.clicked.connect(lambda: self.protocol.reset_password(self.user["email"]))
            self.forgot_password_button.setIcon(QIcon(assets_path + "\\key.svg"))

            self.delete_account_button.clicked.connect(lambda: self.protocol.delete_user(self.user["email"]))
            self.delete_account_button.setIcon(QIcon(assets_path + "\\delete.svg"))

            self.upload_icon_button.clicked.connect(lambda: self.protocol.upload_icon())
            self.upload_icon_button.setIcon(QIcon(assets_path + "\\profile.svg"))

            self.subscriptions_button.clicked.connect(self.subscriptions_page)
            self.subscriptions_button.setIcon(QIcon(assets_path + "\\upgrade.svg"))

            self.change_username_button.clicked.connect(self.protocol.change_username)
            self.change_username_button.setIcon(QIcon(assets_path + "\\change_user.svg"))

            self.back_button.clicked.connect(self.user_page)
            self.back_button.setIcon(QIcon(assets_path + "\\back.svg"))
            
            self.setGeometry(temp)
            self.force_update_window()
        except:
            print(traceback.format_exc())

    def subscriptions_page(self):
        try:
            temp = self.window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/subscription.ui"
            helper.update_ui_size(ui_path, self.window_geometry.width(), self.window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            self.protocol.get_used_storage()
            self.back_button.clicked.connect(self.manage_account)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))

            self.free_button.clicked.connect(lambda: self.protocol.subscribe(0))
            self.basic_button.clicked.connect(lambda: self.protocol.subscribe(1))
            self.premium_button.clicked.connect(lambda: self.protocol.subscribe(2))
            self.professional_button.clicked.connect(lambda: self.protocol.subscribe(3))

            if self.user["subscription_level"] == "0":
                self.free_button.setDisabled(True)
                self.free_button.setText("Selected")
                self.free_button.setStyleSheet("background-color:dimgrey")
            elif self.user["subscription_level"] == "1":
                self.basic_button.setDisabled(True)
                self.basic_button.setText("Selected")
                self.basic_button.setStyleSheet("background-color:dimgrey")
            elif self.user["subscription_level"] == "2":
                self.premium_button.setDisabled(True)
                self.premium_button.setText("Selected")
                self.premium_button.setStyleSheet("background-color:dimgrey")
            elif self.user["subscription_level"] == "3":
                self.professional_button.setDisabled(True)
                self.professional_button.setText("Selected")
                self.professional_button.setStyleSheet("background-color:dimgrey")

            self.storage_remaining.setMaximum(Limits(self.user["subscription_level"]).max_storage)
            self.set_used_storage()
    
            
            self.setGeometry(temp)
            self.force_update_window()
        except:
            print(traceback.format_exc())

    def recovery(self, email):
        try:
            temp = self.window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/recovery.ui"
            helper.update_ui_size(ui_path, self.window_geometry.width(), self.window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
                
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)

            self.password_toggle.clicked.connect(lambda: self.toggle_password(self.password))
            self.confirm_password_toggle.clicked.connect(lambda: self.toggle_password(self.confirm_password))

            self.reset_button.clicked.connect(lambda: self.protocol.password_recovery(email, self.code.text(), self.password.text(), self.confirm_password.text()))
            self.reset_button.setShortcut("Return")
            self.reset_button.setIcon(QIcon(assets_path+"\\reset.svg"))

            self.send_again_button.clicked.connect(lambda: self.protocol.reset_password(email))
            self.send_again_button.setIcon(QIcon(assets_path+"\\again.svg"))

            self.back_button.clicked.connect(self.manage_account)
            self.back_button.setIcon(QIcon(assets_path+"\\back.svg"))
            
            self.setGeometry(temp)
            self.force_update_window()
        except:
            print(traceback.format_exc())
        
    def not_connected_page(self, connect = True):
        try:
            temp = self.window_geometry
            ui_path = f"{os.getcwd()}/gui/ui/not_connected.ui"
            helper.update_ui_size(ui_path, self.window_geometry.width(), self.window_geometry.height())
            uic.loadUi(ui_path, self)
            self.save_sizes()
            self.ip.setText(self.protocol.ip)
            self.port.setText(str(self.protocol.port))
            
            self.connect_button.clicked.connect(lambda: self.protocol.connect_server(self.ip.text(), self.port.text()))
            self.connect_button.setShortcut("Return")
            self.connect_button.setIcon(QIcon(assets_path+"\\connect.svg"))
            
            self.exit_button.clicked.connect(helper.force_exit)
            self.exit_button.setIcon(QIcon(assets_path+"\\exit.svg"))
            
            self.setGeometry(temp)
            self.force_update_window()
            if connect: self.protocol.connect_server(self.protocol.ip, self.protocol.port, True)

        except:
            print(traceback.format_exc())

    def select_item(self, btn):
        item_id = btn.id
        item_name = btn.name
        
        if btn in self.currently_selected and len(self.currently_selected) == 1:
            if btn.is_folder: 
                self.protocol.move_dir(item_id)
                self.reset_selected()
            else: self.protocol.view_file(item_id, item_name, btn.file_size)
        elif helper.control_pressed() and btn not in self.currently_selected:
            self.currently_selected.append(btn)
        elif helper.control_pressed() and btn in self.currently_selected:
            self.currently_selected.remove(btn)
        else:
            self.reset_selected()
            self.currently_selected = [btn]
        
        if btn in self.currently_selected:
            for label in btn.lables:
                label.setObjectName("selected")
        else:
            for label in btn.lables:
                if btn.is_folder: label.setObjectName("folder-label")
                else: label.setObjectName("file-label")
        
        current_stylesheet = self.app.styleSheet()
        # Clear and reapply the stylesheet
        self.app.setStyleSheet("")
        self.app.setStyleSheet(current_stylesheet)
        
        self.force_update_window()

    
    def finish_sending(self):
        self.file_queue = []
        try:
            self.stop_button.setEnabled(False)
            self.stop_button.hide()
        except: pass
        try: self.file_upload_progress.hide()
        except: pass
        self.user_page()

    def update_progress(self, value):
        try: self.file_upload_progress.show()
        except: pass
        try:
            self.stop_button.setEnabled(True)
            self.stop_button.show()
        except: pass
        try: self.file_upload_progress.setValue(value)
        except: pass

    def reset_progress(self, value):
        try: self.file_upload_progress.show()
        except: pass
        try:
            self.stop_button.setEnabled(True)
            self.stop_button.show()
        except: pass
        try: self.file_upload_progress.setMaximum(value)
        except: pass
        
    def reset_selected(self):
        for btn in self.currently_selected:
            for label in btn.lables:
                try:
                    if btn.is_folder: label.setObjectName("folder-label")
                    else: label.setObjectName("file-label")
                except RuntimeError:
                    if label in self.currently_selected: self.currently_selected.remove(label)
        self.currently_selected = []
            
    def confirm_account_deletion(self, email):
            # Create a QApplication instance if needed
            confirm_email = dialogs.new_name_dialog("Delete Account", "Enter account email:")
            if email == confirm_email:
                return True
            else:
                self.set_error_message("Entered email does not match account email")
        
    def activate_file_view(self, file_id):
        save_path = self.files_downloading[file_id].save_location
        file_hash = helper.compute_file_md5(save_path)
        file_viewer_dialog("File Viewer", save_path)

        if file_hash != helper.compute_file_md5(save_path):
            save = dialogs.show_confirmation_dialog("Do you want to save changes?")
            if save:
                self.file_sending.file_queue.extend([save_path])  # Add dropped files to the queue
                self.file_sending.send_files("UPFL", file_id)
            else: os.remove(save_path)
        else: os.remove(save_path)

    def toggle_password(self, text):
        if text.echoMode() == QLineEdit.EchoMode.Normal:
            text.setEchoMode(QLineEdit.EchoMode.Password)
        else:
            text.setEchoMode(QLineEdit.EchoMode.Normal)

    def file_dialog(self):
        try:
            file_paths, _ = QFileDialog.getOpenFileNames(self, "Open File", "", "All Files (*);;Text Files (*.txt)")

            if file_paths:  # Check if any files were selected
                self.file_sending.file_queue.extend(file_paths)  # Add dropped files to the queue
                self.file_sending.send_files()
                    
        except:
            print(traceback.format_exc())
    
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():  # Check if the dragged object is a file (URL)
            event.acceptProposedAction()  # Accept the drag event

    # This function handles when the dragged object is dropped
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
            self.file_sending.file_queue.extend(file_paths)  # Add dropped files to the queue
            self.file_sending.send_files()

    def change_sort(self, new_sort):
        if self.sort == new_sort: self.sort_direction = not self.sort_direction
        self.sort = new_sort
        self.user_page()

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
            if self.share: self.cwd.setText(f"Shared > {" > ".join(self.user['cwd_name'].split("\\"))}"[:-3])
            elif self.deleted: self.cwd.setText(f"Deleted > {" > ".join(self.user['cwd_name'].split("\\"))}"[:-3])
            else: self.cwd.setText(f"{self.user['username']} > {" > ".join(self.user['cwd_name'].split("\\"))}"[:-3])
    
    def set_used_storage(self):
        self.storage_remaining.setValue(int(self.used_storage))
        self.storage_label.setText(f"Storage used ({helper.format_file_size(self.used_storage*1_000_000)} / {Limits(self.user["subscription_level"]).max_storage//1000} GB):")
    
    def stop_upload(self):
        self.stop_button.setEnabled(False)
        if self.file_sending.active_threads != []:
            self.file_sending.active_threads[0].running = False
        self.protocol.send_data(b"STOP|" + self.uploading_file_id.encode())

    def force_update_window(self):
        size = self.size()
        resize_event = QResizeEvent(size, size)
        self.resizeEvent(resize_event)
    
    def update_current_files(self):
        self.sort_widget.currentIndexChanged.disconnect()
        if self.sort == "Name" or not self.share and self.sort == "Owner":
            self.sort_widget.setCurrentIndex(0)
        elif self.sort == "Date":
            self.sort_widget.setCurrentIndex(1)
        elif self.sort == "Type":
            self.sort_widget.setCurrentIndex(2)
        elif self.sort_widget == "Size":
            self.sort_widget.setCurrentIndex(3)
        elif self.share and self.sort == "Owner":
            self.sort_widget.setCurrentIndex(4) 

        self.save_sizes()
        self.draw_cwd()
        self.sort_widget.currentIndexChanged.connect(lambda: self.change_sort(self.sort_widget.currentText()[1:]))    
        self.scroll.verticalScrollBar().setMaximum(self.scroll_progress)
        self.scroll.verticalScrollBar().setValue(self.scroll_progress)
        self.scroll.verticalScrollBar().valueChanged.connect(self.scroll_changed)
        
    def share_file(self, file_id, user_cred, file_name, read = "False", write = "False", delete = "False", rename = "False", download = "False", share = "False"):
        temp_app = QApplication.instance()  # Use existing QApplication
        if temp_app is None:
            temp_app = QApplication([])  # Create a new instance if it doesn't exist

        dialog = QDialog()
        dialog.setWindowTitle("File Share Options")
        dialog.setStyleSheet("font-size:15px;")
        dialog.resize(600, 400)

        # Group the checkboxes for better organization
        permissions_group = QGroupBox(f"File sharing premission of {file_name} with {user_cred}")
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
        submit_btn.clicked.connect(lambda: self.protocol.send_share_premissions(
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
    
    def check_all_perms(self, perm):
        for button in self.currently_selected:
            if button.perms[perm] != "True": return False
        return True

    def check_all_id(self):
        for button in self.currently_selected:
            if button.id == None: return False
        return True

    def remove_selected(self, button):
        if button in self.currently_selected: self.currently_selected.remove(button)






class FileButton(QPushButton):
    def __init__(self, window, text, id = None, parent=None, is_folder = False, shared_by = None, perms =["True", "True","True","True","True","True"], size = 0, name=""):
        super().__init__("|".join(text), parent)
        self.setText = "|".join(text)
        self.id = id
        self.is_folder = is_folder
        self.shared_by = shared_by
        self.perms = perms
        self.setMinimumHeight(30)
        self.file_size = size
        self.name = name
        self.lables = []
        self.window = window

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to align with button edges
        button_layout.setSpacing(0)
        for i, label_text in enumerate(text):
            label = QLabel(label_text)
            if i == 0:
                if self.is_folder:
                    label.setText(f'&nbsp;<img src="{assets_path + "\\folder.svg"}" width="20" height="20"><label>&nbsp;{helper.truncate_label(label, label_text)}</label>')
                elif self.id is not None:
                    icon_path = assets_path + "\\file_types\\" + helper.format_file_type(label_text.split("~")[0].split(".")[-1][:-1]) + ".svg"
                    if not os.path.isfile(icon_path): icon_path = assets_path + "\\file.svg"
                    label.setText(f'&nbsp;<img src="{icon_path}" width="16" height="20">&nbsp;{helper.truncate_label(label, label_text)}')
            if self.id is None: 
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if label_text != "Back" and label_text != "No files or folders in this directory":
                    if i == 0: b_sort = "Name"
                    elif i == 1: b_sort = "Date"
                    #elif i == 2: b_sort = "Type"
                    elif i == 2: b_sort = "Size"
                    elif i == 3: b_sort = "Owner"
                    label.mousePressEvent  =  lambda event, sort_key=b_sort: self.window.change_sort(sort_key)
                    if b_sort ==  self.window.sort:
                        label.setText(f'<img src="{assets_path}\\{'asc.svg' if  self.window.sort_direction else 'dsc.svg'}" width="20" height="20"><label>&nbsp;&nbsp;{label_text}</label>')
            if self.is_folder: label.setObjectName("folder-label")
            elif self.id != None: label.setObjectName("file-label")
            elif label_text == "Back": label.setObjectName("back-label")
            button_layout.addWidget(label, stretch=1)
            self.lables.append(label)
        button_layout.setStretch(0, 2)  # First label takes 2 parts
        for i in range(1, len(text)):
            button_layout.setStretch(i, 1)  # Other labels take 1 part each

        self.setLayout(button_layout)

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)

        if  self.window.check_all_id() and  self.window.check_all_perms(4) and not  self.window.deleted and self.window.currently_selected != []:
            action = menu.addAction(" Download")
            action.triggered.connect(self.window.protocol.download)
            action.setIcon(QIcon(assets_path + "\\download.svg"))

        if  self.window.check_all_id() and self.window.currently_selected != []:
            if  self.window.check_all_perms(2):
                if  self.window.deleted and  self.window.user["cwd"] != "": pass
                else:
                    action = menu.addAction(" Delete")
                    action.triggered.connect(self.window.protocol.delete)
                    action.setIcon(QIcon(assets_path + "\\delete.svg"))

            if  self.window.check_all_perms(3) and not  self.window.deleted and len(self.window.currently_selected) == 1:
                action = menu.addAction(" Rename")
                action.triggered.connect(self.rename)
                action.setIcon(QIcon(assets_path + "\\change_user.svg"))
            
            if  self.window.check_all_perms(5) and not  self.window.deleted:
                action = menu.addAction(" Share")
                action.triggered.connect( self.window.protocol.share_action)
                action.setIcon(QIcon(assets_path + "\\share.svg"))
            
            if self.window.share and self.window.user["cwd"] == "" and not self.window.deleted:
                action = menu.addAction(" Remove")
                action.triggered.connect(self.window.protocol.remove)
                action.setIcon(QIcon(assets_path + "\\remove.svg"))

        if not self.window.share and not self.window.deleted:
            action = menu.addAction(" New Folder")
            action.triggered.connect(self.window.protocol.new_folder)
            action.setIcon(QIcon(assets_path + "\\new_account.svg"))
        
        if self.window.deleted and self.window.user["cwd"] == "" and self.window.currently_selected != []:
            action = menu.addAction(" Recover")
            action.triggered.connect(self.window.protocol.recover)
            action.setIcon(QIcon(assets_path + "\\new_account.svg"))

        action = menu.addAction(" Search")
        action.triggered.connect(self.window.protocol.search)
        action.setIcon(QIcon(assets_path + "\\search.svg"))

        menu.exec(event.globalPos())
            
    def rename(self):
        name = self.text().split(" | ")[0][1:]
        new_name = dialogs.new_name_dialog("Rename", "Enter new file name:", name)
        if new_name is not None:
            self.window.protocol.send_data(b"RENA|" + self.id.encode() + b"|" + name.encode() + b"|" + new_name.encode())




