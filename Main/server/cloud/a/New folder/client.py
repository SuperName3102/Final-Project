import socket
import sys
import threading
import json
from PyQt6.QtWidgets import QApplication

from main_controller import MainController
from consts import *
from chess_pieces import Coordinates


class ChessClient:
    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.controller = MainController(self)
        self.connected_clients = []
        self.turn = WHITE

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

        client_thread = threading.Thread(target=self.listen_for_messages)
        client_thread.start()

    def listen_for_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode(UTF_8)
                if message:
                    print(f'[CLIENT] RECEIVED MESSAGE FROM [SERVER]: {message}')
                    data = json.loads(message)
                    self.handle_server_message(data)

            except Exception as e:
                print(f'[CLIENT] ERROR RECEIVING MESSAGE FOR [SERVER]: {e}')
                break

    def handle_server_message(self, data):
        if data[TYPE] == SIGN_UP:
            self.controller.handle_sign_up_response(data)

        elif data[TYPE] == SIGN_IN:
            self.controller.handle_sign_in_response(data)

        elif data[TYPE] == COLOR_SELECTION:
            self.controller.handle_color_selection_response(data[STATUS])

        elif data[TYPE] == MOVE:
            if data[USERNAME] == self.controller.username:
                if self.turn == WHITE:
                    self.turn = BLACK
                elif self.turn == BLACK:
                    self.turn = WHITE
                return
            self.controller.update_board_with_move(data[PIECE_TYPE], data[COLOR], Coordinates(data[SOURCE_COORDS][0], data[SOURCE_COORDS][1]), Coordinates(data[DEST_COORDS][0], data[DEST_COORDS][1]))

    def send_message(self, message):
        try:
            self.client_socket.send(json.dumps(message).encode(UTF_8))

        except Exception as e:
            print(f'[CLIENT] ERROR SENDING MESSAGE TO [SERVER]: {e}')

    def send_move(self, piece_type, source_coords, dest_coords):
        message = {
            TYPE: MOVE,
            USERNAME: self.controller.username,
            COLOR: piece_type.split('-')[0],
            PIECE_TYPE: piece_type,
            SOURCE_COORDS: source_coords,
            DEST_COORDS: dest_coords,
            TURN: self.turn
        }
        self.send_message(message)


def main():
    app = QApplication(sys.argv)
    client = ChessClient()
    client.controller.show_main_page()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
