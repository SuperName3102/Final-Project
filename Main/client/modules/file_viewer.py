# 2024 © Idan Hazay


from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtGui import QPixmap
import os
from docx import Document
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QImage
import fitz  # PyMuPDF for PDF handling
import traceback


class PDFViewerDialog(QDialog):
    def __init__(self, title, file_path):
        super().__init__()
        self.setWindowTitle(title)
        self.layout = QVBoxLayout()

        self.file_path = file_path
        self.pdf_document = fitz.open(file_path)
        self.current_page = 0  # Start on the first page
        self.total_pages = self.pdf_document.page_count

        self.content_widget = QLabel(self)

        # Navigation buttons
        self.navigation_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous", self)
        self.next_button = QPushButton("Next", self)
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)

        # Close button
        self.close_button = QPushButton('Close', self)
        self.close_button.clicked.connect(self.close)

        # Add widgets to layout
        self.navigation_layout.addWidget(self.prev_button)
        self.navigation_layout.addWidget(self.next_button)
        self.layout.addLayout(self.navigation_layout)
        self.layout.addWidget(self.content_widget)
        self.layout.addWidget(self.close_button)

        self.setLayout(self.layout)

        # Display the first page
        self.show_page(self.current_page)

    def show_page(self, page_number):
        """Display the specified page of the PDF."""
        try:
            page = self.pdf_document.load_page(page_number)  # Load the requested page
            pix = page.get_pixmap()  # Get the pixmap

            # Check if the pixmap has an alpha channel
            if pix.alpha:
                # Create an RGB image from the Pixmap without the alpha channel
                pix = fitz.Pixmap(pix, 0)  # Convert to RGB
            
            # Convert the pixmap to a QImage
            image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)

            # Display the PDF page as an image
            self.content_widget.setPixmap(QPixmap.fromImage(image).scaled(600, 800, Qt.AspectRatioMode.KeepAspectRatio))
        except Exception as e:
            print(traceback.format_exc())
            self.content_widget.setText(f"Error displaying page {page_number + 1}: {str(e)}")

    def next_page(self):
        """Go to the next page if available."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def prev_page(self):
        """Go to the previous page if available."""
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

    def closeEvent(self, event):
        """Close the PDF document when the dialog is closed."""
        self.pdf_document.close()
        event.accept()


def file_viewer_dialog(title, file_path):
    app = QApplication.instance()  # Use existing QApplication

    file_extension = os.path.splitext(file_path)[1].lower()

    # If the file is a PDF, use the PDFViewerDialog class
    if file_extension == '.pdf':
        dialog = PDFViewerDialog(title, file_path)
        return True
    else:
        dialog = QDialog()
        layout = QVBoxLayout()

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
            content_widget.setPixmap(pixmap.scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio))  # Scaling
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


        # Fallback: Try to open any file as plain text
        else:
            content_widget = QTextEdit(dialog)
            content_widget.setReadOnly(True)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content_widget.setPlainText(file.read())
            except Exception as e:
                content_widget.setPlainText(f"Unsupported file type {file_extension}")
            layout.insertWidget(0, content_widget)

        dialog.setLayout(layout)
        dialog.exec()