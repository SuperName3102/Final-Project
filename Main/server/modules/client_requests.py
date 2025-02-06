# 2024 © Idan Hazay
# Import libraries

from modules import database_handling

from email.message import EmailMessage
from datetime import datetime, timedelta

import ssl, smtplib, os, bcrypt, secrets, uuid, traceback, zipfile, io, random


class User:
    """
    User class for building database
    Used to transfer between user instance and json data
    """

    def __init__(self, id, email, username, password, salt=bcrypt.gensalt(), last_code=-1, valid_until=None, verified=False, subscription_level = 0, admin_level = 0, cookie = "", cookie_expiration = -1):
        if id is None:
            self.id = ClientRequests().gen_user_id()
        else:
            self.id = id
        self.email = email
        self.username = username
        self.password = password
        self.salt = salt
        self.last_code = last_code
        if valid_until == None:
            valid_until = str(datetime.now())
        self.valid_until = valid_until
        self.verified = verified
        self.subscription_level = subscription_level
        self.admin_level = admin_level
        self.cookie = cookie
        self.cookie_expiration = cookie_expiration

class File:
    """
    User class for building database
    Used to transfer between user instance and json data
    """

    def __init__(self, id, sname, fname, parent, owner_id, size, last_edit = None):
        if id is None:
            self.id = ClientRequests().gen_file_id()
        else:
            self.id = id
    
        if sname is None:
            self.sname = ClientRequests().gen_file_name()
        else:
            self.sname = sname
        self.fname = fname
        self.parent = parent
        self.owner_id = owner_id
        self.size = size
        if last_edit == None:
            last_edit = str(datetime.now())
        self.last_edit = last_edit

class Directory:
    def __init__(self, id, name, parent, owner_id):
        if id is None:
            self.id = ClientRequests().gen_file_id()
        else:
            self.id = id
        self.name = name
        self.parent = parent
        self.owner_id = owner_id


class ClientRequests:
    def __init__(self):
        self.pepper_file = f"{os.path.dirname(os.path.abspath(__file__))}\\pepper.txt"
        self.server_path = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}"
        self.gmail = "idancyber3102@gmail.com"
        self.gmail_password = "nkjg eaom gzne nyfa"
        self.get_pepper()
        self.db = database_handling.DataBase()
    
    def get_pepper(self):
        if (not os.path.isfile(self.pepper_file)):
            new_pepper = secrets.token_hex(2000)
            with open(self.pepper_file, 'wb') as file:
                file.write(new_pepper)
        with open(self.pepper_file, 'rb') as file:
            self.pepper = file.read()

    def user_exists(self, username):
        """
        Checking if username is already registered
        """
        user = self.db.get_user(username)
        if user != None:
            return True
        else:
            return False


    def verified(self, cred):
        """
        Checking if user is verified
        """
        user = self.db.get_user(cred)
        if (user == None):
            return False
        user = User(**user)
        return user.verified


    def email_registered(self, email):
        """
        Checking if email address is already registered under an account 
        """
        user = self.db.get_user(email)
        if user != None:
            return True
        else:
            return False


    def login_validation(self, cred, password):
        """
        Checking if login details match user in database
        """
        user = self.db.get_user(cred)
        if (user == None):
            return False
        user = User(**user)
        if (user.password == self.hash_password(password, user.salt)):
            return True
        else:
            return False


    def signup_user(self, user_details):
        """
        Creating new user in database
        From user instance
        """
        new_user = User(None, *user_details)
        new_user.password = self.hash_password(new_user.password, new_user.salt)
        new_user.cookie = self.generate_cookie(new_user.id)
        self.db.add_user(vars(new_user))


    def verify_user(self, email):
        """
        Verifying user
        """
        id = self.db.get_user_id(email)
        self.db.update_user(id, "verified", True)


    def delete_user(self, id):
        """
        Deleting user from database
        """
        files = self.db.get_files(id)
        for file in files:
            try:
                file = File(**file)
                os.remove(self.server_path + "\\cloud\\" + file.sname)
            except:
                print(traceback.format_exc())
                continue
        if os.path.exists(f"{self.server_path}\\user icons\\{id}.ico"):
            os.remove(f"{self.server_path}\\user icons\\{id}.ico")
        
        self.db.remove_user(id)
        
        


    def send_reset_mail(self, email):
        """
        Sending password reset email
        Generating random 6 digit code
        Assigning it to user 
        Add expiry time
        """
        id = self.db.get_user_id(email)
        code = random.randint(100000, 999999)
        valid_until = str(timedelta(minutes=10) + datetime.now())
        self.db.update_user(id, ["last_code", "valid_until"], [code, valid_until])

        em = EmailMessage()   # Building mail and sending it
        em["From"] = self.gmail
        em["To"] = email
        em["Subject"] = "Password reset code"
        body = f"Your password reset code is: {code}\nCode is valid for 10 minutes"
        em.set_content(body)
        self.send_mail(em, email)


    def send_verification(self, email):
        """
        Sending account verification email
        Generating random 6 digit code
        Assigning it to user 
        Add expiry time
        """

        # Setting new code and updating user
        id = self.db.get_user_id(email)
        code = random.randint(100000, 999999)
        valid_until = str(timedelta(minutes=30) + datetime.now())
        self.db.update_user(id, ["last_code", "valid_until"], [code, valid_until])

        em = EmailMessage()   # Building mail and sending it
        em["From"] = self.gmail
        em["To"] = email
        em["Subject"] = "Account Verification"
        body = f"Your account verification code is: {code}\nCode is valid for 30 minutes"
        em.set_content(body)
        self.send_mail(em, email)


    def send_welcome_mail(self, email):
        em = EmailMessage()   # Building mail and sending it
        em["From"] = self.gmail
        em["To"] = email
        em["Subject"] = "Welcome!"
        body = f"""Welcome to IdanCloud!\nCurrently you are at the basic subscription level and are welcome to upgrade at any time
        \nYou have 100 GB of storage and a max file size of 50 MB, max upload speed of 5 MB/s and 10 MB/s download speed\nFor any question you are welcome to contact us at {self.gmail}
        \nIdanCloud ©2024 - 2025"""
        em.set_content(body)
        self.send_mail(em, email)


    def send_mail(self, em, send_to):
        """
        Sending email to email address
        Using SMTP secure connection
        """
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp_server:
            smtp_server.login(self.gmail, self.gmail_password)
            smtp_server.sendmail(self.gmail, send_to, em.as_string())


    def check_code(self, email, code):
        """
        Check the code provided by user
        Works for user verification and password recovery
        """
        user = self.db.get_user(email)
        if (user == None):
            return False
        user = User(**user)

        if (self.str_to_date(user.valid_until) < datetime.now()):
            return "time"
        elif (not code.isdigit() or int(user.last_code) != int(code) or int(code) < 0):
            return "code"
        else:
            return "ok"


    def hash_password(self, password, salt):
        hashed_password = bcrypt.hashpw(password.encode() + self.pepper, salt)
        return hashed_password


    def change_password(self, email, new_password):
        """
        Changing user password
        Hashing the password with salf and pepper for security
        Updating the users database
        """
        id = self.db.get_user_id(email)
        salt = bcrypt.gensalt()
        password = self.hash_password(new_password, salt)
        self.db.update_user(id, ["salt", "password"], [salt, password])


    def get_user_data(self, cred):
        """
        Getting the user data
        To use in server.py which doesnt have direct access to db
        """
        return self.db.get_user(cred)



    def get_files(self, owner_id, parent, name_filter=None):
        if parent == "":
            files = self.db.get_user_files(owner_id)
        else:
            files = self.db.get_files(parent)
        parsed_files = []
        for file in files:
            file = File(**file)
            if (name_filter is None or name_filter.lower() in file.fname.lower()) and file.parent == parent and not self.is_deleted(file.id):
                last_edit = self.str_to_date(file.last_edit)
                if file.owner_id == owner_id:
                    to_add = f"{file.fname}~{last_edit}~{file.size}~{file.id}"
                else:
                    to_add = f"{file.fname}~{last_edit}~{file.size}~{file.id}~{"".join((self.db.get_user_values(file.owner_id, ["username"])))}"
                    to_add += "~" + "~".join(self.get_perms(owner_id, file.id))
                parsed_files.append(to_add)
            
        return parsed_files


    def get_directories(self, owner_id, parent, name_filter=None):
        if parent == "":
            directories = self.db.get_user_directories(owner_id)
        else:
            directories = self.db.get_directories(parent)
        parsed_directories = []
        for directory in directories:
            directory = Directory(**directory)
            if (name_filter is None or name_filter.lower() in directory.name.lower()) and directory.parent == parent and not self.is_deleted(directory.id):
                size = self.directory_size(directory.owner_id, directory.id)
                last_change = self.get_directory_last_change(directory.id)
                if last_change == datetime.min: last_change = ""
                if directory.owner_id == owner_id:
                    to_add = f"{directory.name}~{directory.id}~{last_change}~{size}"
                else:
                    to_add = f"{directory.name}~{directory.id}~{last_change}~{size}~{"".join((self.db.get_user_values(directory.owner_id, ["username"])))}"
                    to_add += "~" + "~".join(self.get_perms(owner_id, directory.id))
                parsed_directories.append(to_add)
        
        return parsed_directories
            
    def get_directory_last_change(self, id, lastest_edit = datetime.min):
        for directory in self.db.get_directories(id):
            directory = Directory(**directory)
            lastest_edit = max(lastest_edit, self.get_directory_last_change(directory.id, lastest_edit))
        files = self.db.get_files(id)
        if files is None:
            return lastest_edit
        for file in files:
            file = File(**file)
            current_last_change = self.str_to_date(file.last_edit)
            if current_last_change > lastest_edit:
                lastest_edit = current_last_change
        return lastest_edit
            

    def change_level(self, id, new_level):
        self.db.update_user(id, "subscription_level", new_level)


    def change_username(self, id, new_username):
        self.db.update_user(id, "username", new_username)

    def generate_cookie(self, id):
        cookie = str(secrets.token_hex(256))
        while self.db.get_user(cookie) is not None:
            cookie = str(secrets.token_hex(256))
        cookie_expiration =  str(timedelta(weeks=4) + datetime.now())
        self.db.update_user(id, ["cookie", "cookie_expiration"], [cookie, cookie_expiration])

    def get_cookie(self, id):
        return self.db.get_user_values(id, ["cookie"])[0]

    def cookie_expired(self, id):
        user = self.db.get_user(id)
        if (user == None):
            return True
        user = User(**user)
        return (self.str_to_date(user.cookie_expiration) < datetime.now())

    def get_user_id(self, cred):
        return self.db.get_user_id(cred)

    def new_file(self, sname, file_name, parent, owner_id, size):
        file = File(None, sname, file_name, parent, owner_id, size)
        self.db.add_file(vars(file))

    def get_file_id(self, file_name):
        file = self.db.get_file(file_name)
        if (file == None):
            return None
        file = File(**file)
        return file.id

    def get_file_sname(self, file_id):
        file = self.db.get_file(file_id)
        if (file == None):
            return None
        file = File(**file)
        return file.sname

    def get_file_fname(self, file_id):
        file = self.db.get_file(file_id)
        if (file == None):
            return None
        file = File(**file)
        return file.fname

    def is_file_owner(self, owner_id, file_id):
        file = self.db.get_file(file_id)
        if (file == None):
            return None
        file = File(**file)
        return file.owner_id == owner_id

    def is_dir_owner(self, owner_id, dir_id):
        if dir_id == "":
            return True
        directory = self.db.get_directory(dir_id)
        if (directory == None):
            return None
        directory = Directory(**directory)
        return directory.owner_id == owner_id  

    def rename_file(self, id, new_name):
        self.db.update_file(id, ["fname"], new_name)

    def update_file_size(self, file_id, new_size):
        self.db.update_file(file_id, "size", new_size)

    def rename_directory(self, id, new_name):
        self.db.update_directory(id, ["name"], new_name)

    def delete_file(self, id):
        sname = self.get_file_sname(id)
        if os.path.exists(f"{self.server_path}\\cloud\\{sname}") and self.db.delete_file(id):
            os.remove(f"{self.server_path}\\cloud\\{sname}")

    def create_folder(self, name, parent, owner_id):
        directory = Directory(None, name, parent, owner_id)
        self.db.add_directory(vars(directory))


    def valid_directory(self, directory_id, user_id):
        directory = self.db.get_directory(directory_id)
        if (directory == None):
            return False
        directory = Directory(**directory)
        return directory.owner_id == user_id or self.is_shared(user_id, directory_id)

    def is_shared(self, user_id, directory_id):
        directory = self.db.get_directory(directory_id)
        if (directory == None):
            return False
        directory = Directory(**directory)
        shared_dir = self.db.get_share_file(directory_id, user_id)
        while shared_dir is None:
            directory = self.db.get_directory(directory.parent)
            if (directory == None):
                return False
            directory = Directory(**directory)
            directory_id = directory.id
            shared_dir = self.db.get_share_file(directory_id, user_id)
        return True
        

    def get_dir_name(self, id):
        if id == "":
            return ""
        directory = self.db.get_directory(id)
        if (directory == None):
            return None
        directory = Directory(**directory)
        return directory.name

    def get_parent_directory(self, id):
        if id == "":
            return ""
        directory = self.db.get_directory(id)
        if (directory == None):
            return None
        directory = Directory(**directory)
        return directory.parent

    def get_file_parent_directory(self, id):
        if id == "":
            return ""
        file = self.db.get_file(id)
        if (file == None):
            return None
        file = File(**file)
        return file.parent

    def get_full_path(self, id):
        if id == "":
            return ""
        path = [""]
        
        directory = self.db.get_directory(id)
        if (directory == None):
            return None
        directory = Directory(**directory)
        path.append(directory.name)
        while directory.parent != "":
            directory = self.db.get_directory(directory.parent)
            if (directory == None):
                return None
            directory = Directory(**directory)
            path.append(directory.name)
        path = "\\".join(path[::-1])
        return path
        
    def delete_directory(self, id):
        sub_dirs = self.db.get_sub_directories(id)
        if sub_dirs != []:
            for sub_dir in sub_dirs:
                self.delete_directory(sub_dir["id"])

        files = self.db.get_directory_files(id)
        if self.db.delete_directory(id):
            for file in files:
                try:
                    file = File(**file)
                    os.remove(self.server_path + "\\cloud\\" + file.sname)
                except:
                    print(traceback.format_exc())
                    continue


    def directory_size(self, user_id, id):
        total = 0
        files = self.db.get_user_directory_files(user_id, id)
        
        for file in files:
            try:
                file = File(**file)
                if os.path.exists(self.server_path + "\\cloud\\" + file.sname):
                    total += os.path.getsize(self.server_path + "\\cloud\\" + file.sname)
            except:
                print(traceback.format_exc())
                continue
        child_dirs = self.db.get_directories(id)
        for child_dir in child_dirs:
            total += self.directory_size(user_id, child_dir["id"])
        return total

    def get_user_storage(self, id):
        return self.directory_size(id, "")
        
    def clean_db(self, files_uploading):
        for name in os.listdir(self.server_path + "\\cloud"):
            try:
                if self.db.get_file(name) is None and self.db.get_user(name) is None and not any(obj.name == name for obj in files_uploading.values()):
                    os.remove(self.server_path + "\\cloud\\" + name)
            except:
                print(traceback.format_exc())
                continue
        db_files =self.db.get_all_files()
        for file in db_files:
            try:
                if not os.path.exists(self.server_path + "\\cloud\\" + file["sname"]) or (self.db.get_directory(file["parent"]) is None and file["parent"] != ""):
                    self.db.delete_file(file["id"])
                    self.db.delete_file(file["id"])
                elif self.is_deleted(file["id"]) and self.str_to_date(self.db.get_deleted_time(file["id"])[0]) < datetime.now():
                    self.db.delete_file(file["id"])
            except:
                print(traceback.format_exc())
                continue
        db_directories = self.db.get_all_directories()
        for directory in db_directories:
            try:
                if self.db.get_user(directory["owner_id"]) is None or (self.db.get_directory(directory["parent"]) is None and directory["parent"] != ""):
                    self.db.delete_directory(directory["id"])
                    self.db.delete_directory(directory["id"])
            except:
                print(traceback.format_exc())
                continue

    def get_share_options(self, file_id, user_cred):
        user_id = self.db.get_user_id(user_cred)
        file = self.db.get_share_file(file_id, user_id)
        return file
        
    def share_file(self, file_id, user_cred, perms):
        user_id = self.db.get_user_id(user_cred)
        share = self.db.get_share_file(file_id, user_id)
        if user_id is None:
            return
        if share is None:
            id = self.gen_perms_id()
            file = self.db.get_file(file_id)
            directory = self.db.get_directory(file_id)
            if (file != None):
                file = File(**file)
                self.db.create_share(id, file.owner_id, file_id, user_id, perms)
            elif (directory != None):
                directory = Directory(**directory)
                self.db.create_share(id, directory.owner_id, file_id, user_id, perms)
        else:
            self.db.update_sharing_premissions(file_id, user_id, perms)

    def get_share_files(self, user_id, parent, name_filter=None):
        files = self.db.get_all_share_files(user_id)
        parsed_files = []
        for file in files:
            file = File(**file)
            if ((name_filter is None or name_filter.lower() in file.fname.lower()) and not self.is_deleted(file.id)):
                try:
                    last_edit = self.str_to_date(file.last_edit)
                    parsed_files.append(f"{file.fname}~{last_edit}~{file.size}~{file.id}~{"".join((self.db.get_user_values(file.owner_id, ["username"])))}~{"~".join(self.get_perms(user_id, file.id))}")
                except: continue
        return parsed_files

    def get_share_directories(self, user_id, parent, name_filter=None):
        directories = self.db.get_all_share_directories(user_id)
        parsed_directories = []
        for directory in directories:
            directory = Directory(**directory)
            if ((name_filter is None or name_filter.lower() in directory.name.lower()) and not self.is_deleted(directory.id)):
                owner_name = "".join((self.db.get_user_values(directory.owner_id, ["username"])))
                size = self.directory_size(directory.owner_id, directory.id)
                last_change = self.get_directory_last_change(directory.id)
                if last_change == datetime.min: last_change = ""
                parsed_directories.append(f"{directory.name}~{directory.id}~{last_change}~{size}~{owner_name}~{"~".join(self.get_perms(user_id, directory.id))}")

        return parsed_directories

    def get_deleted_files(self, user_id, parent, name_filter=None):
        files = self.db.get_deleted_files(user_id)
        parsed_files = []
        for file in files:
            file = File(**file)
            if (name_filter is None or name_filter.lower() in file.fname.lower()):
                last_edit = self.str_to_date(file.last_edit)
                parsed_files.append(f"{file.fname}~{last_edit}~{file.size}~{file.id}")
            
        return parsed_files


    def get_deleted_directories(self, user_id, parent, name_filter=None):
        directories = self.db.get_deleted_directories(user_id)
        parsed_directories = []
        for directory in directories:
            directory = Directory(**directory)
            if (name_filter is None or name_filter.lower() in directory.name.lower()):
                size = self.directory_size(directory.owner_id, directory.id)
                last_change = self.db.get_deleted_time(directory.id)[0]
                if last_change == datetime.min: last_change = ""
                parsed_directories.append(f"{directory.name}~{directory.id}~{last_change}~{size}")

        return parsed_directories

    def is_shared_directory(self, user_id, directory_id):
        directory = self.db.get_directory(directory_id)
        if (directory == None):
            return None
        directory = Directory(**directory)
        shared_dir = self.db.get_share_file(directory_id, user_id)
        while shared_dir is None:
            directory = self.db.get_directory(directory.parent)
            if (directory == None):
                return None
            directory = Directory(**directory)
            directory_id = directory.id
            shared_dir = self.db.get_share_file(directory_id, user_id)
        return directory_id

    def is_shared_file(self, user_id, file_id):
        parent = self.get_file_parent_directory(file_id)
        return self.is_shared_directory(user_id, parent)

    def remove_share(self, user_id, id):
        self.db.remove_share(user_id, id)

    def can_read(self, user_id, id):
        perms = self.get_perms(user_id, id)
        return self.is_file_owner(user_id, id) or self.is_dir_owner(user_id, id) or (perms != None and perms[0] == "True")

    def can_write(self, user_id, id):
        perms = self.get_perms(user_id, id)
        return self.is_file_owner(user_id, id) or self.is_dir_owner(user_id, id) or (perms != None and perms[1] == "True")

    def can_delete(self, user_id, id):
        perms = self.get_perms(user_id, id)
        return self.is_file_owner(user_id, id) or self.is_dir_owner(user_id, id) or (perms != None and perms[2] == "True")

    def can_rename(self, user_id, id):
        perms = self.get_perms(user_id, id)
        return self.is_file_owner(user_id, id) or self.is_dir_owner(user_id, id) or (perms != None and perms[3] == "True")

    def can_download(self, user_id, id):
        perms = self.get_perms(user_id, id)
        return self.is_file_owner(user_id, id) or self.is_dir_owner(user_id, id) or (perms != None and perms[4] == "True")

    def can_share(self, user_id, id):
        perms = self.get_perms(user_id, id)
        return self.is_file_owner(user_id, id) or self.is_dir_owner(user_id, id) or (perms != None and perms[5] == "True")

    def get_perms(self, user_id, id):
        perms = self.db.get_file_perms(user_id, id)
        if perms is None:
            perms = self.db.get_file_perms(user_id, self.is_shared_directory(user_id, id))
        if perms is None:
            perms = self.db.get_file_perms(user_id, self.is_shared_file(user_id, id))
        return perms
            


    def zip_files(self, ids):
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_id in ids:
                # Check if it's a file or a directory
                if self.get_file_sname(file_id) is not None:
                    # It's a file
                    file_path = self.server_path + "\\cloud\\" + self.get_file_sname(file_id)
                    file_name = self.get_file_fname(file_id)
                    zf.write(file_path, file_name)
                elif self.get_dir_name(file_id) is not None:
                    # It's a directory, use zip_directory to add its contents
                    directory_buffer = self.zip_directory(file_id)
                    with zipfile.ZipFile(directory_buffer, 'r') as dir_zip:
                        for name in dir_zip.namelist():
                            dir_name = self.get_dir_name(file_id)
                            # Maintain folder structure by writing with its directory name
                            zf.writestr(f"{dir_name}/{name}", dir_zip.read(name))
            
            # Reset the buffer position to the beginning and send the zip
        zip_buffer.seek(0)
        return zip_buffer

    def zip_directory(self, directory_id):
        """
        Create a zip file containing all files and directories in the specified directory.
        
        :param db_path: Path to the sqlite3 database.
        :param directory_id: The ID of the directory to zip.
        :param output_zip: The path of the output zip file.
        """
        
        # Get the contents of the directory
        directory_contents = self.db.get_directory_contents(directory_id)
        
        # Create the zip file
        zip_buffer = io.BytesIO()
        
        # Create the zip file in memory
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for full_path, relative_path in directory_contents:
                zf.write(full_path, relative_path)
        
        # Move the buffer's position to the beginning so it can be read
        zip_buffer.seek(0)
        return zip_buffer


    def is_deleted(self, id):
        return self.db.get_deleted(id) != None

    def recover(self, id):
        self.db.recover(id)
    
    
    def gen_user_id(self):
        id = uuid.uuid4().hex
        while self.db.get_user(id) is not None:
            id = uuid.uuid4().hex
        return id

    def gen_file_id(self):
        id = uuid.uuid4().hex
        while self.db.get_file(id) is not None:
            id = uuid.uuid4().hex
        return id

    def gen_file_name(self):
        name = uuid.uuid4().hex
        while self.db.get_file(name) is not None:
            name = uuid.uuid4().hex
        return name

    def gen_perms_id(self):
        name = uuid.uuid4().hex
        while self.db.get_perms(name) is not None:
            name = uuid.uuid4().hex
        return name
    
    @staticmethod
    def str_to_date(str):
        """
        Transfer string of date to date
        Helper function
        """
        if str == "": return datetime.min
        format = "%Y-%m-%d %H:%M:%S.%f"
        return datetime.strptime(str, format)
