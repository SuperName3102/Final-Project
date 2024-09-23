# 2024 © Idan Hazay

from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QFileDialog
from PyQt6.QtGui import QPixmap
import sys
import os
from docx import Document
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon



def file_viewer_dialog(title, file_path):
    app = QApplication.instance()  # Use existing QApplication
    dialog = QDialog()
    if (os.path.isfile(f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/assets/icon.ico")):
        dialog.setWindowIcon(QIcon(f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/assets/icon.ico"))

    dialog.setWindowTitle(title)
    layout = QVBoxLayout()

    close_button = QPushButton('Close', dialog)
    close_button.clicked.connect(dialog.close)

    layout.addWidget(close_button)

    content_widget = None
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
        content_widget = QLabel(dialog)
        pixmap = QPixmap(file_path)
        content_widget.setPixmap(pixmap.scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio))  # Scaling
        layout.insertWidget(0, content_widget)
    elif file_extension == '.docx':
        content_widget = QTextEdit(dialog)
        content_widget.setReadOnly(True)
        try:
            doc = Document(file_path)
            full_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            content_widget.setPlainText(full_text)
        except Exception as e:
            content_widget.setPlainText(f"Error reading document: {str(e)}")
        layout.insertWidget(0, content_widget)
    else:
        content_widget = QLabel(dialog)
        content_widget.setText(f"Unsupported file type: {file_extension}")
        layout.insertWidget(0, content_widget)
    # Set the layout for the dialog
    dialog.setLayout(layout)
    dialog.exec()
    return True