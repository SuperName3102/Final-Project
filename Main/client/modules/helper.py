# 2024 © Idan Hazay
from datetime import datetime
import xml.etree.ElementTree as ET

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