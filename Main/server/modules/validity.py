# 2024 © Idan Hazay

import re


# Begin validation checking related functions 
class Validation:
    def __init__(self):
        self.illegal_chars = {'\'', '"', '>', '<', '~', '`', '|', '\\','/', '}', '{', '[', ']', '+', '=', ';', '(', ')'}
    def is_valid_email(self, email):
        """
        Check if email is valid with regex
        """
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if(re.match(email_regex, email) is not None):
            return True
        else:
            return False


    def is_valid_username(self, username):
        """
        Check if username is valid
        Has to be at least 4 long
        Only letters and numbers
        """
        if(len(username) >= 4 and username.isalnum()):
            return True
        else:
            return False

    def is_valid_password(self, password):
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

    def is_empty(self, list):
        """
        Checking list of strings for empty string
        """
        for item in list:
            if item == "":
                return True
        return False

    def has_illegal_chars(self, input_str):
        """
        Check if string has any of the illegal chars
        Illegal chars listed above in global vars
        """
        if(any(char in self.illegal_chars for char in input_str)):
            return True
        return False

    def check_illegal_chars(self, string_list):
        """
        Check if list of strings contains any illegal char
        Uses the has_illegal_chars function
        """
        return any(self.has_illegal_chars(s) for s in string_list)