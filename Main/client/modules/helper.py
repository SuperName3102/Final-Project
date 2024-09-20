# 2024 © Idan Hazay


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