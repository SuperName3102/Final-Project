# 2024 © Idan Hazay

import re

illegal_chars = {'\'', '"', '>', '<', '~', '`', '|', '\\','/', '}', '{', '[', ']', '+', '=', ';', '(', ')'}


# Begin validation checking related functions 

def is_valid_email(email):
    """
    Check if email is valid with regex
    """
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if(re.match(email_regex, email) is not None):
        return True
    else:
        return False


def is_valid_username(username):
    """
    Check if username is valid
    Has to be at least 4 long
    Only letters and numbers
    """
    if(len(username) >= 4 and username.isalnum()):
        return True
    else:
        return False

def is_valid_password(password):
    """
    Check if username is valid
    Has to be at least 8 long
    Has to contain upper letter
    Has to contain numbers
    """
    if(len(password) >= 8 and any(char.isupper() for char in password) and any(char.isdigit() for char in password)):
        return True
    else:
        return False

def is_empty(list):
    """
    Checking list of strings for empty string
    """
    for item in list:
        if item == "":
            return True
    return False

def has_illegal_chars(input_str):
    """
    Check if string has any of the illegal chars
    Illegal chars listed above in global vars
    """
    if(any(char in illegal_chars for char in input_str)):
        return True
    return False

def check_illegal_chars(string_list):
    """
    Check if list of strings contains any illegal char
    Uses the has_illegal_chars function
    """
    return any(has_illegal_chars(s) for s in string_list)