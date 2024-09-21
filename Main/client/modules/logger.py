# 2024 © Idan Hazay

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename=f"{os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))}\\app_log.txt",
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class Logger:
    def __init__(self):
        self.terminal = sys.stdout

    def write(self, message):
        if message.strip():  # Log non-empty messages
            logging.info(message.strip())

    def flush(self):
        pass  # For compatibility with some IO operations that may expect flush
