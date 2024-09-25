# 2024 © Idan Hazay
# Import libraries

from . import database_handling as db

import random
from email.message import EmailMessage
import ssl
import smtplib
import os
import bcrypt
from datetime import datetime, timedelta
import secrets
from pathlib import Path
import uuid


pepper_file = f"{os.path.dirname(os.path.abspath(__file__))}\\pepper.txt"
gmail = "idancyber3102@gmail.com"
gmail_password = "nkjg eaom gzne nyfa"

pepper = secrets.token_hex(32)


class User:
    """
    User class for building database
    Used to transfer between user instance and json data
    """

    def __init__(self, id, email, username, password, salt=bcrypt.gensalt(), last_code=-1, valid_until=str(datetime.now()), verified=False, subscription_level = 0, admin_level = 0):
        if id is None:
            self.id = gen_id()
        else:
            self.id = id
        self.email = email
        self.username = username
        self.password = password
        self.salt = salt
        self.last_code = last_code
        self.valid_until = valid_until
        self.verified = verified
        self.subscription_level = subscription_level
        self.admin_level = admin_level

def gen_id():
    id = uuid.uuid4().hex
    while db.get_user(id) is not None:
        id = uuid.uuid4().hex
    return id

def main():
    global pepper
    pepper = get_pepper()


def get_pepper():
    if (not os.path.isfile(pepper_file)):
        new_pepper = secrets.token_hex(2000)
        with open(pepper_file, 'w') as file:
            file.write(new_pepper)
    with open(pepper_file, 'r') as file:
        pepper = file.read()
    return pepper.encode()

# Begin client requests related functions


def user_exists(username):
    """
    Checking if username is already registered
    """
    user = db.get_user(username)
    if user != None:
        return True
    else:
        return False


def verified(cred):
    """
    Checking if user is verified
    """
    user = db.get_user(cred)
    if (user == None):
        return False
    user = User(**user)
    return user.verified


def email_registered(email):
    """
    Checking if email address is already registered under an account 
    """
    user = db.get_user(email)
    if user != None:
        return True
    else:
        return False


def login_validation(cred, password):
    """
    Checking if login details match user in database
    """
    user = db.get_user(cred)
    if (user == None):
        return False
    user = User(**user)
    if (user.password == hash_password(password, user.salt)):
        return True
    else:
        return False


def signup_user(user_details):
    """
    Creating new user in database
    From user instance
    """
    new_user = User(None, *user_details)
    new_user.password = hash_password(new_user.password, new_user.salt)
    db.add_user(vars(new_user))


def verify_user(username):
    """
    Verifying user
    """
    user = db.get_user(username)
    if (user == None):
        return False
    user = User(**user)
    user.verified = True
    db.update_user(username, vars(user))


def delete_user(username):
    """
    Deleting user from database
    """
    db.remove_user(username)


def send_reset_mail(email):
    """
    Sending password reset email
    Generating random 6 digit code
    Assigning it to user 
    Add expiry time
    """
    user = db.get_user(email)
    if (user == None):
        return False
    user = User(**user)
    # Setting new code and updating user
    code = random.randint(100000, 999999)
    user.last_code = code
    user.valid_until = str(timedelta(minutes=10) + datetime.now())
    db.update_user(email, vars(user))

    em = EmailMessage()   # Building mail and sending it
    em["From"] = gmail
    em["To"] = email
    em["Subject"] = "Password reset code"
    body = f"Your password reset code is: {code}\nCode is valid for 10 minutes"
    em.set_content(body)
    send_mail(em, email)


def send_verification(email):
    """
    Sending account verification email
    Generating random 6 digit code
    Assigning it to user 
    Add expiry time
    """
    user = db.get_user(email)
    if (user == None):
        return False
    user = User(**user)
    # Setting new code and updating user
    code = random.randint(100000, 999999)
    user.last_code = code
    user.valid_until = str(timedelta(minutes=30) + datetime.now())
    db.update_user(email, vars(user))

    em = EmailMessage()   # Building mail and sending it
    em["From"] = gmail
    em["To"] = email
    em["Subject"] = "Account Verification"
    body = f"Your account verification code is: {
        code}\nCode is valid for 30 minutes"
    em.set_content(body)
    send_mail(em, email)


def send_welcome_mail(email):
    em = EmailMessage()   # Building mail and sending it
    em["From"] = gmail
    em["To"] = email
    em["Subject"] = "Welcome!"
    body = f"""Welcome to IdanCloud!\nCurrently you are at the basic subscription level and are welcome to upgrade at any time
    \nYou have 100 GB of storage and a max file size of 50 MB, max upload speed of 5 MB/s and 10 MB/s download speed\nFor any question you are welcome to contact us at {gmail}
    \nIdanCloud ©2024 - 2025"""
    em.set_content(body)
    send_mail(em, email)


def send_mail(em, send_to):
    """
    Sending email to email address
    Using SMTP secure connection
    """
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp_server:
        smtp_server.login(gmail, gmail_password)
        smtp_server.sendmail(gmail, send_to, em.as_string())


def check_code(email, code):
    """
    Check the code provided by user
    Works for user verification and password recovery
    """
    user = db.get_user(email)
    if (user == None):
        return False
    user = User(**user)

    if (str_to_date(user.valid_until) < datetime.now()):
        return "time"
    elif (not code.isdigit() or int(user.last_code) != int(code) or int(code) < 0):
        return "code"
    else:
        return "ok"


def hash_password(password, salt):
    hashed_password = bcrypt.hashpw(password.encode() + pepper, salt)
    return hashed_password


def str_to_date(str):
    """
    Transfer string of date to date
    Helper function
    """
    format = "%Y-%m-%d %H:%M:%S.%f"
    return datetime.strptime(str, format)


def change_password(email, new_password):
    """
    Changing user password
    Hashing the password with salf and pepper for security
    Updating the users database
    """
    user = db.get_user(email)
    if (user == None):
        return False
    user = User(**user)
    user.salt = bcrypt.gensalt()
    user.password = hash_password(new_password, user.salt)
    db.update_user(email, vars(user))


def get_user_data(cred):
    """
    Getting the user data
    To use in server.py which doesnt have direct access to db
    """
    return db.get_user(cred)


def get_files(path, name_filter=None):
    files = []
    if os.path.isdir(path):
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                # Apply the filter if provided
                if name_filter is None or name_filter.lower() in f.lower():
                    file_mod_time = os.path.getmtime(os.path.join(path, f))
                    mod_time_datetime = datetime.fromtimestamp(file_mod_time)
                    last_edit = mod_time_datetime.strftime('%d/%m/%Y %H:%M')

                    files.append(f"{f}~{last_edit}~{
                                 os.path.getsize(os.path.join(path, f))}")
    return files


def get_directories(path, name_filter=None):
    if not os.path.isdir(path):
        return []
    return [
        f.name for f in os.scandir(path)
        if f.is_dir() and (name_filter is None or name_filter.lower() in f.name.lower())
    ]


def is_subpath(parent_path, sub_path):
    # Convert to Path objects
    parent_path = Path(parent_path).resolve()
    sub_path = Path(sub_path).resolve()

    # Check if sub_path is within parent_path
    return parent_path in sub_path.parents or parent_path == sub_path


def change_level(email, new_level):
    user = db.get_user(email)
    if (user == None):
        return False
    user = User(**user)
    user.subscription_level = new_level
    db.update_user(email, vars(user))


def change_username(username, new_username):
    user = db.get_user(username)
    if (user == None):
        return False
    user = User(**user)
    user.username = new_username
    db.update_user(username, vars(user))


if __name__ == "__main__":
    main()

# add manual user
# main()
# salt = bcrypt.gensalt()
# password = hash_password("a", salt)
# delete_user("a")
# db.add_user(vars(User("a", "a", password, salt, verified=True)))
