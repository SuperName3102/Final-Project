import sys
from PyQt6 import QtWidgets, uic
import os

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/ui/main.ui", self)
        
        # Connect the button to a method
        self.signup_button.clicked.connect(self.signup_action)
        self.login_button.clicked.connect(self.login_page)
        
    def signup_action(self):
        print("signup")
    
    def login_page(self):
        uic.loadUi(f"{os.path.dirname(os.path.abspath(__file__))}/ui/login.ui", self)
        self.login_button.clicked.connect(self.login)
    
    
    def login(self):
        name = self.user.toPlainText()
        password = self.password.toPlainText()
        print(name, password)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/css/style.css", 'r') as f:
        app.setStyleSheet(f.read())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())