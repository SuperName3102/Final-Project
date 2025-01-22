# 2024 © Idan Hazay
# Import libraries

from modules.dialogs import *
from modules.helper import *

from modules.logger import Logger
from modules.file_viewer import *
from modules.config import *
from modules import networking, receive, gui

import socket, sys, traceback, time, functools

from PyQt6 import QtWidgets

# Announce global vars
ip = "127.0.0.1"
port = 31026

last_msg = ""
last_error_msg = ""

def timing_decorator(func):
    @functools.wraps(func)  # Preserves the original function's metadata
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()  # Start the timer
        result = func(*args, **kwargs)   # Call the original function
        end_time = time.perf_counter()  # End the timer
        print(f"Function '{func.__name__}' took {end_time - start_time:.4f} seconds")
        return result
    return wrapper



class Application():
    def __init__(self):
        sys.excepthook = self.global_exception_handler
        self.qtapp = QtWidgets.QApplication(sys.argv)
        
        self.network = networking.Network()
        self.window = gui.MainWindow(self.qtapp, self.network)
        self.start_app()
        sys.exit(self.qtapp.exec())
        
    def start_app(self):
        self.window.show()
        self.window.not_connected_page(False)
        self.receive_thread = receive.ReceiveThread(self.network)
        self.receive_thread.reply_received.connect(self.handle_reply)
        self.window.receive_thread = self.receive_thread
        self.window.protocol.connect_server(ip, port, True)


    def handle_reply(self, reply):
        """
        Getting server reply and parsing it
        If some error occured or no response disconnect
        """
        try:
            self.network.logtcp('recv', reply)

            to_show = self.window.protocol.protocol_parse_reply(reply)
            print(to_show)
            if to_show == "Invalid reply from server":
                print(reply)
            
            # If exit request succeded, dissconnect
            if to_show == "Server acknowledged the exit message":
                print('Succefully exit')
                self.network.sock.close()
                sys.exit()
        except socket.error as err:   # General error handling
            print(traceback.format_exc())
            return
        except Exception as err:
            print(traceback.format_exc())
            return

    
    def global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(f"Unhandled exception:\n{error_message}")

        QMessageBox.critical(
            None,
            "Application Error",
            f"An unexpected error occurred:\n\n{exc_value}",
            QMessageBox.StandardButton.Ok,
        )





def main():
    """
    Main function
    Create tkinter root and start secure connection to server
    Connect to server via addr param
    """
    global app
    app = Application()


if __name__ == "__main__":   # Run main
    sys.stdout = Logger()
    main()

