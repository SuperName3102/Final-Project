# 2024 © Idan Hazay
# Import libraries

import os, traceback
from PyQt6.QtWidgets import QMessageBox, QApplication, QInputDialog
from PyQt6.QtGui import QIcon


def new_name_dialog(title, label, text=""):
    """Display an input dialog for the user to enter a new name."""
    app = QApplication.instance()  # Get existing QApplication instance
    app.setWindowIcon(QIcon(f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/assets/icon.ico"))  # Set window icon
    
    dialog = QInputDialog()
    dialog.setStyleSheet("font-size:18px;")
    dialog.setWindowTitle(title)
    dialog.setLabelText(label)
    dialog.setTextValue(text)
    dialog.resize(400, 300)  # Resize dialog to 400x300

    ok = dialog.exec()  # Show the dialog and wait for user input

    if ok == QInputDialog.DialogCode.Accepted:
        folder_name = dialog.textValue()
        if folder_name and folder_name != text:
            return folder_name  # Return input if it's not empty or unchanged


def show_confirmation_dialog(message):
    """Display a confirmation dialog with Yes/No options."""
    msg_box = QMessageBox()
    msg_box.setStyleSheet("font-size:18px;")
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setWindowTitle("Confirmation")
    msg_box.setText(message)

    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
    result = msg_box.exec()  # Show the dialog and wait for user input

    return result == QMessageBox.StandardButton.Yes  # Return True if user clicks Yes


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions by displaying an error message."""
    error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"Unhandled exception:\n{error_message}")

    QMessageBox.critical(
        None,
        "Application Error",
        f"An unexpected error occurred:\n\n{exc_value}",
        QMessageBox.StandardButton.Ok,
    )