# 2024 © Idan Hazay
# Import libraries

from datetime import datetime
import xml.etree.ElementTree as ET
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics, QGuiApplication
import hashlib, os, json, sys

class JsonHandle():
    def __init__(self):
        self.uploading_files_json = f"{os.getcwd()}/cache/uploading_files.json"
        self.downloading_files_json = f"{os.getcwd()}/cache/downloading_files.json"
    
    
    def get_files_uploading_data(self):
        if os.path.exists(self.uploading_files_json):
            with open(self.uploading_files_json, 'r') as f:
                return json.load(f)

    def get_files_downloading_data(self):
        if os.path.exists(self.downloading_files_json):
            with open(self.downloading_files_json, 'r') as f:
                return json.load(f)
    
    def update_json(self, upload, file_id, file_path, remove=False, file = None, progress = 0):
        """Update the JSON file with the file upload details."""
        if upload: json_path = self.uploading_files_json
        else: json_path = self.downloading_files_json
        if not os.path.exists(os.getcwd() + "\\cache"):
            os.makedirs(os.getcwd() + "\\cache")
        if not os.path.exists(json_path):
            with open(json_path, 'w') as f:
                json.dump({}, f)  # Initialize as an empty dictionary

        with open(json_path, 'r') as f:
            files = json.load(f)

        if remove:
            # Remove the file from JSON if it exists
            if file_id in files:
                del files[file_id]
        else:
            if file == None: files[file_id] = {"file_path": file_path}
            else: 
                files[file_id] = {
                "file_path": file_path,
                "size": file.size,
                "is_view": file.is_view,
                "file_name": file.file_name,
                "progress": progress
            }

        with open(json_path, 'w') as f:
            json.dump(files, f, indent=4)

def force_exit():
    sys.exit()


def control_pressed():
    modifiers = QGuiApplication.queryKeyboardModifiers()
    return modifiers & Qt.KeyboardModifier.ControlModifier

def build_req_string(code, values = []):
    """
    Builds a request string
    Gets string code and list of string values
    """
    send_string = code
    for value in values:
        send_string += "|"
        send_string += value
    return send_string.encode()

def format_file_size(size):
    if size < 10_000:  # Less than 10,000 bytes
        return f"{size:,} B"
    elif size < 10_000_000:  # Between 10,001 and 10,000,000 bytes (in KB)
        return f"{size / 1_000:,.2f} KB"
    elif size < 10_000_000_001:  # Between 10,000,001 and 10,000,000,000 bytes (in MB)
        return f"{size / 1_000_000:,.2f} MB"
    elif size < 10_000_000_000_001:  # Between 10,000,000,001 and 10,000,000,000,000 bytes (in GB)
        return f"{size / 1_000_000_000:,.2f} GB"
    else:  # Above 10,000,000,000,001 bytes (in TB)
        return f"{size / 1_000_000_000_000:,.2f} TB"
    
def parse_file_size(size_str):
    units = {
        "B": 1,
        "KB": 1_000,
        "MB": 1_000_000,
        "GB": 1_000_000_000,
        "TB": 1_000_000_000_000,
    }
    unit = size_str.split(" ")[1]
    size = size_str.split(" ")[0]
    if unit in units.keys():
        return int(float(size) * units[unit])
    return 0

def str_to_date(str):
    """
    Transfer string of date to date
    Helper function
    """
    if str == "": return datetime.min
    format = "%Y-%m-%d %H:%M:%S.%f"
    return datetime.strptime(str, format)


def update_ui_size(ui_file, new_width, new_height):
    # Parse the XML file
    tree = ET.parse(ui_file)
    root = tree.getroot()
    
    # Find the geometry property
    for widget in root.findall(".//widget[@class='QMainWindow']"):
        geometry = widget.find("property[@name='geometry']/rect")
        if geometry is not None:
            # Update width and height
            width_elem = geometry.find("width")
            height_elem = geometry.find("height")
            if width_elem is not None and height_elem is not None:
                width_elem.text = str(new_width)
                height_elem.text = str(new_height)
    
    # Save the modified XML back to the .ui file
    tree.write(ui_file, encoding='utf-8', xml_declaration=True)
    
    
def truncate_label(label, text):
    font_metrics = QFontMetrics(label.font())
    max_width = int(label.width()//1.9)

        # Check if the text fits
    if font_metrics.horizontalAdvance(text) > max_width:
            # Truncate the text with ellipsis
        truncated_text = font_metrics.elidedText(text, Qt.TextElideMode.ElideRight, max_width)
        return truncated_text
    return text

file_types = {
    "zip": ["rar"],
    "png": ["jpg", "jpeg", "jfif", "gif", "ico"],
    "mp3": ["wav"],
    "code": ["py", "js", "cs", "c", "cpp", "jar"],
    "txt": ["css"]
}
def format_file_type(type):
    for extention in file_types.keys():
        if type in file_types[extention] or type == extention:
            return extention
    return type

def compute_file_md5(file_path):
    hash_func = hashlib.new('md5')
    with open(file_path, 'rb') as file:
        while chunk := file.read(8192):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()