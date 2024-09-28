# 2024 © Idan Hazay

from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtGui import QPixmap
import os
from docx import Document
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon



def open_in_native_app(file_path):
    """Try to open the file with the default system application."""
    try:
        os.startfile(file_path)
    except Exception as e:
        print(f"Error opening file in native app: {e}")


def file_viewer_dialog(title, file_path):
    app = QApplication.instance()  # Use existing QApplication
    if app is None:
        app = QApplication([])  # Create a new instance if it doesn't exist

    file_extension = os.path.splitext(file_path)[1].lower()
    dialog = QDialog()
    layout = QVBoxLayout()
    dialog.resize(600, 400)

    # Set window icon if available
    icon_path = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/assets/icon.ico"
    if os.path.isfile(icon_path):
        dialog.setWindowIcon(QIcon(icon_path))

    dialog.setWindowTitle(title)

    close_button = QPushButton('Close', dialog)
    close_button.clicked.connect(dialog.close)
    layout.addWidget(close_button)

    content_widget = None

    # Handle image files
    if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
        content_widget = QLabel(dialog)
        pixmap = QPixmap(file_path)
        content_widget.setPixmap(pixmap.scaled(600, 800, Qt.AspectRatioMode.KeepAspectRatio))
        layout.insertWidget(0, content_widget)

        # Handle .docx files
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
        # Unsupported file type, try to open in native app
        content_widget = QLabel(dialog)
        content_widget.setText(f"Cannot open {"".join(file_path.split("\\")[-1].split("-")[1:])} in file viewer\nTry opening it in its defualt app")
        content_widget.setStyleSheet("font-size: 20px")
        content_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.insertWidget(0, content_widget)

        # Button to open in native app
        open_native_button = QPushButton(f"Open {file_extension} in default app", dialog)
        open_native_button.clicked.connect(lambda: open_in_native_app(file_path))
        layout.addWidget(open_native_button)

    dialog.setLayout(layout)
    dialog.exec()