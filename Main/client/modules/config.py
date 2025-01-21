# 2024 © Idan Hazay

import traceback, os
from PyQt6.QtCore import QRect

len_field = 4
chunk_size = 524288
user_icon = f"{os.getcwd()}/assets/user.ico"
assets_path = f"{os.getcwd()}/assets"
cookie_path = f"{os.getcwd()}/cookies/user.cookie"


saved_ip = "127.0.0.1"
saved_port = 31026


items_to_load = 20
scroll_size = [850, 340]
window_geometry = QRect(350, 200, 1000, 550)



