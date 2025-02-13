import os
import glob
import pdfkit
import sys
from PyPDF2 import PdfMerger

def convert_py_to_pdf(folder_path):
    if not os.path.exists(folder_path):
        print("Folder not found")
        return

    py_files = []
    for root, dirs, files in os.walk(folder_path):
        # Skip 'venv' folder if it exists
        if 'venv' in dirs:
            dirs.remove('venv')
        py_files += glob.glob(os.path.join(root, '*.py'))
        py_files += glob.glob(os.path.join(root, '*.pyw'))
    if not py_files:
        print(".py files not found")
        return

    pdf_folder = os.path.join('pdf_files')
    os.makedirs(pdf_folder, exist_ok=True)

    # Specify the path to the wkhtmltopdf executable file
    config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')

    # Define an inline style (e.g., font-size: 12px).
    # You can adjust font-size or font-family to your liking.
    style_block = """
    <style>
    body {
        font-family: "Courier New", monospace;
        font-size: 12px; /* Adjust the size as needed */
        margin: 20px;
    }
    pre {
        white-space: pre-wrap; /* Ensures long lines wrap */
        word-wrap: break-word; /* Breaks words if needed */
    }
    </style>
    """

    for py_file in py_files:
        py_file_name = os.path.basename(py_file)
        pdf_file_name = os.path.splitext(py_file_name)[0] + '.pdf'
        pdf_file_path = os.path.join(pdf_folder, pdf_file_name)

        with open(py_file, 'r', encoding='utf-8') as file:
            py_code = file.read()

        # Escape certain HTML characters and wrap in <pre>
        escaped_code = (
            py_code
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        
        # Build a simple HTML document
        html_content = f"""
        <html>
        <head>{style_block}</head>
        <body>
            <pre>{escaped_code}</pre>
        </body>
        </html>
        """

        # Convert HTML string to PDF
        pdfkit.from_string(html_content, pdf_file_path, configuration=config)

        print(f"File {pdf_file_name} created")

    print("Conversion completed")

def merge_pdfs(input_folder, output_path):
    merger = PdfMerger()
    input_files = glob.glob(f"{input_folder}/*.pdf")

    for path in input_files:
        merger.append(path)

    merger.write(output_path)
    merger.close()

if __name__ == "__main__":
    try:
        args = sys.argv
        folder_path = args[1]
    except:
        folder_path = "C:\\Users\\idanh\\Desktop\\Cyber\\My Projects\\Final Project"
    convert_py_to_pdf(folder_path)

    input_folder = 'pdf_files'
    output_file = 'merged.pdf'
    merge_pdfs(input_folder, output_file)
