# 2024 © Idan Hazay logger_s.py

import os, sys, logging

# Configure logging
logging.basicConfig(
    filename=f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}\\app_log.txt",
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class Logger:
    """
    Class to log all prints into file
    """
    def __init__(self):
        self.terminal = sys.stdout  # Store the original stdout so we can still print to console
        sys.stdout = self  # Redirect sys.stdout to the Logger instance

    def write(self, message):
        if message.strip():  # Log non-empty messages
            logging.info(message.strip())
            self.terminal.write(message + "\n")  # Also write the message to the console

    def flush(self):
        self.terminal.flush()  # Make sure to flush stdout buffer for compatibility
