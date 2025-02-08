# 2024 © Idan Hazay

# Global libraries
import traceback, os
from PyQt6.QtCore import QRect

# Global variables
LEN_FIELD = 4
CHUNK_SIZE = 524288
SOCK_TIMEOUT = 0.3
USER_ICON = f"{os.getcwd()}/assets/user.ico"
ASSETS_PATH = f"{os.getcwd()}/assets"
COOKIE_PATH = f"{os.getcwd()}/cookies/user.cookie"

SAVED_IP = "192.168.1.122"
SAVED_PORT = 3102

ITEMS_TO_LOAD = 20
SCROLL_SIZE = [850, 340]
WINDOW_GEOMERTY = QRect(350, 200, 1000, 550)



