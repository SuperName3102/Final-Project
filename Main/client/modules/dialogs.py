# 2024 © Idan Hazay

import os
from PyQt6.QtWidgets import QMessageBox, QApplication, QInputDialog
from PyQt6.QtGui import QIcon


def new_name_dialog(title, label, text=""):
    # Create a QApplication instance
    app = QApplication.instance()
    app.setWindowIcon(QIcon(f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/assets/icon.ico"))
    dialog = QInputDialog()
    dialog.setWindowTitle(title)
    dialog.setLabelText(label)
    dialog.setTextValue(text)
    dialog.resize(300, 300)  # Resize dialog to 300x200

    # Get the text input
    ok = dialog.exec()  # Show the dialog modally and wait for user input

    # Check if the user clicked OK and returned valid text
    if ok == QInputDialog.DialogCode.Accepted:
        folder_name = dialog.textValue()
        if folder_name and folder_name != text:
            return folder_name


def show_confirmation_dialog(message):
    # Create a QMessageBox
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setWindowTitle("Confirmation")
    msg_box.setText(message)

    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
    result = msg_box.exec()

    if result == QMessageBox.StandardButton.Yes:
        return True
    else:
        return False
