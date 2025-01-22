# 2024 © Idan Hazay
# Import libraries

import os, sqlite3, traceback
from datetime import datetime, timedelta

class DataBase:
    def __init__(self):
        self.database = f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}\\server\\database\\database.db"
        self.users_table = "Users"
        self.files_table = "Files"
        self.permissions_table = "Permissions"
        self.directories_table = "Directories"
        self.deleted_table = "Deleted"

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        #cursor.execute(f"DROP TABLE {users_table}")
        #cursor.execute(f"DROP TABLE {files_table}")
        #cursor.execute(f"DROP TABLE {directories_table}")
        #cursor.execute(f"DROP TABLE {permissions_table}")
        cursor.execute(f"DROP TABLE {self.deleted_table}")
        #cursor.execute(f"CREATE TABLE IF NOT EXISTS {users_table} (id TEXT PRIMARY KEY, email TEXT UNIQUE, username TEXT UNIQUE, password TEXT, salt TEXT, last_code INTEGER, valid_until TEXT, verified BOOL, subscription_level INT, admin_level INT, cookie TEXT UNIQUE, cookie_expiration TEXT)")
        #cursor.execute(f"CREATE TABLE IF NOT EXISTS {files_table} (id TEXT PRIMARY KEY, sname TEXT UNIQUE, fname TEXT, parent TEXT, owner_id TEXT, size TEXT, last_edit TEXT)")
        #cursor.execute(f"CREATE TABLE IF NOT EXISTS {directories_table} (id TEXT PRIMARY KEY, name TEXT, parent TEXT, owner_id TEXT)")
        #cursor.execute(f"CREATE TABLE IF NOT EXISTS {permissions_table} (id TEXT PRIMARY KEY,  file_id TEXT, owner_id TEXT, user_id TEXT, read BOOL, write BOOL, del BOOL, rename BOOL, download BOOL, share BOOL)")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.deleted_table} (id TEXT PRIMARY KEY, owner_id TEXT, time_to_delete TEXT)")
        conn.commit()
        conn.close()

    def get_user_id(self, cred):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM {self.users_table} WHERE username = ? or email = ?", (cred, cred))
        row = cursor.fetchone()
        conn.close()
        if row == None: return None
        return row[0]


    def add_user(self, user_dict):
        """
        Adding user to database
        Gets dict returns nothing
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        columns = ', '.join(user_dict.keys())
        values = ', '.join(['?'] * len(user_dict))
        sql = f"INSERT INTO {self.users_table} ({columns}) VALUES ({values})"   # Insert all dict values and keys to database
        try:
            cursor.execute(sql, list(user_dict.values()))
            conn.commit()
        except sqlite3.IntegrityError:
            print(traceback.format_exc())
            print("Key values already exist in table")
        conn.close()

    def remove_user(self, id):
        """
        Removing user from database
        Recieves a cred (username or password)
        Returns nothing
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {self.users_table} WHERE id = ?", (id,))
        cursor.execute(f"DELETE FROM {self.files_table} WHERE owner_id = ?", (id,))
        cursor.execute(f"DELETE FROM {self.directories_table} WHERE owner_id = ?", (id,))
        cursor.execute(f"DELETE FROM {self.permissions_table} WHERE owner_id = ?", (id,))
        cursor.execute(f"DELETE FROM {self.permissions_table} WHERE user_id = ?", (id,))
        conn.commit()
        conn.close()



    def update_user(self, id, fields, new_values):
        """
        Update user with new user dict
        Recieves a dict returns nothing
        Removing user and adding the updated one
        (May change in the future for better option)
        """
        if(type(fields) != type([])): fields = [fields]
        if(type(new_values) != type([])): new_values = [new_values]
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        sql = f"UPDATE {self.users_table} SET "
        for field in fields[:-1]:
            sql += f"{field} = ?, "
        sql += f"{fields[-1]} = ? WHERE id = ?"
        try:
            cursor.execute(sql, tuple(new_values + [id]))
            conn.commit()
        except sqlite3.IntegrityError:
            print("Key values already exist in table")
            conn.close()
        conn.close()

    def get_user_values(self, id, fields):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        sql = f"SELECT "
        for field in fields[:-1]:
            sql += f"{field}, "
        sql += f"{fields[-1]} "
        sql += f"FROM {self.users_table} WHERE id = ?"
        cursor.execute(sql, (id,))
        row = cursor.fetchone()
        conn.commit()
        conn.close()
        return row


    def row_to_dict_user(self, row):
        """
        Gets a row of table and returns a dict with that row
        """
        user_dict = {"id": row[0], "email": row[1], "username": row[2], "password": row[3],"salt": row[4],"last_code": row[5],"valid_until": row[6],"verified": bool(row[7]), "subscription_level": int(row[8]), "admin_level": int(row[9]), "cookie": row[10], "cookie_expiration": row[11]}
        return user_dict

    def row_to_dict_file(self, row):
        """
        Gets a row of table and returns a dict with that row
        """
        file_dict = {"id": row[0], "sname": row[1], "fname": row[2], "parent": row[3], "owner_id": row[4], "size": row[5], "last_edit": row[6]}
        return file_dict

    def row_to_dict_directory(self, row):
        """
        Gets a row of table and returns a dict with that row
        """
        directory_dict = {"id": row[0], "name": row[1], "parent": row[2], "owner_id": row[3]}
        return directory_dict

    def get_user(self, cred):
        """
        Returns the user
        Gets cred (username or password)
        Returns dict of user
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.users_table} WHERE username = ? or email = ? or id = ? or cookie = ?", (cred, cred, cred, cred))
        row = cursor.fetchone()
        conn.close()
        if row == None: return None
        return self.row_to_dict_user(row)


    def update_file(self, id, fields, new_values):
        """
        Update user with new user dict
        Recieves a dict returns nothing
        Removing user and adding the updated one
        (May change in the future for better option)
        """
        if(type(fields) != type([])): fields = [fields]
        if(type(new_values) != type([])): new_values = [new_values]
        fields.append("last_edit")
        new_values.append(str(datetime.now()))
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        sql = f"UPDATE {self.files_table} SET "
        for field in fields[:-1]:
            sql += f"{field} = ?, "
        sql += f"{fields[-1]} = ? WHERE id = ?"
        try:
            cursor.execute(sql, tuple(new_values + [id]))
            conn.commit()
        except sqlite3.IntegrityError:
            print("Key values already exist in table")
            conn.close()
        conn.close()

    def get_file(self, cred):
        """
        Returns the user
        Gets cred (username or password)
        Returns dict of user
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.files_table} WHERE id = ? or sname = ?", (cred, cred))
        row = cursor.fetchone()
        conn.close()
        if row == None: return None
        return self.row_to_dict_file(row)

    def get_user_files(self, owner_id):
        """
        Returns the user
        Gets cred (username or password)
        Returns dict of user
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.files_table} WHERE owner_id = ?", (owner_id,))
        ans = cursor.fetchall()
        conn.close()
        files = []
        for file in ans:
            files.append(self.row_to_dict_file(file))
        return files


    def get_files(self, parent):
        """
        Returns the user
        Gets cred (username or password)
        Returns dict of user
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.files_table} WHERE parent = ?", (parent,))
        ans = cursor.fetchall()
        conn.close()
        files = []
        for file in ans:
            files.append(self.row_to_dict_file(file))
        return files

    def add_file(self, file_dict):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        columns = ', '.join(file_dict.keys())
        values = ', '.join(['?'] * len(file_dict))
        sql = f"INSERT INTO {self.files_table} ({columns}) VALUES ({values})"   # Insert all dict values and keys to database
        try:
            cursor.execute(sql, list(file_dict.values()))
            conn.commit()
        except sqlite3.IntegrityError:
            print("Key values already exist in table")
            conn.close()
        conn.close()
        
    def delete_file(self, id):
        """
        Removing user from database
        Recieves a cred (username or password)
        Returns nothing
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {self.deleted_table} WHERE id = ?", (id,))
        ans = cursor.fetchall()
        if ans == []:
            sql = f"INSERT INTO {self.deleted_table} (id, owner_id, time_to_delete) VALUES (?, ?, ?)"
            cursor.execute(sql, [id, self.get_file(id)["owner_id"], str(timedelta(days=30) + datetime.now())])
            conn.commit()
            conn.close()
            return False
        else:
            cursor.execute(f"DELETE FROM {self.files_table} WHERE id = ?", (id,))
            cursor.execute(f"DELETE FROM {self.permissions_table} WHERE file_id = ?", (id,))
            cursor.execute(f"DELETE FROM {self.deleted_table} WHERE id = ?", (id,))
            conn.commit()
            conn.close()
            return True

    def get_all_files(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.files_table}")
        ans = cursor.fetchall()
        conn.close()
        files = []
        for file in ans:
            files.append(self.row_to_dict_file(file))
        return files

    def add_directory(self, directory_dict):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        columns = ', '.join(directory_dict.keys())
        values = ', '.join(['?'] * len(directory_dict))
        sql = f"INSERT INTO {self.directories_table} ({columns}) VALUES ({values})"   # Insert all dict values and keys to database
        try:
            cursor.execute(sql, list(directory_dict.values()))
            conn.commit()
        except sqlite3.IntegrityError:
            print("Key values already exist in table")
            conn.close()
        conn.close()

    def get_user_directories(self, owner_id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.directories_table} WHERE owner_id = ?", (owner_id,))
        ans = cursor.fetchall()
        conn.close()
        directories = []
        for directory in ans:
            directories.append(self.row_to_dict_directory(directory))
        return directories

    def get_directories(self, parent):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.directories_table} WHERE parent = ?", (parent,))
        ans = cursor.fetchall()
        conn.close()
        directories = []
        for directory in ans:
            directories.append(self.row_to_dict_directory(directory))
        return directories

    def get_directory(self, id):
        """
        Returns the user
        Gets cred (username or password)
        Returns dict of user
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.directories_table} WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        if row == None: return None
        return self.row_to_dict_directory(row)

    def delete_directory(self, id):
        """
        Removing user from database
        Recieves a cred (username or password)
        Returns nothing
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.deleted_table} WHERE id = ?", (id,))
        ans = cursor.fetchall()
        if ans == []:
            sql = f"INSERT INTO {self.deleted_table} (id, owner_id, time_to_delete) VALUES (?, ?, ?)"
            cursor.execute(sql, [id, self.get_directory(id)["owner_id"], str(timedelta(days=30) + datetime.now())])
            conn.commit()
            conn.close()
            return False
        else:
            cursor.execute(f"DELETE FROM {self.directories_table} WHERE id = ?", (id,))
            cursor.execute(f"DELETE FROM {self.files_table} WHERE parent = ?", (id,))
            cursor.execute(f"DELETE FROM {self.permissions_table} WHERE file_id = ?", (id,))
            cursor.execute(f"DELETE FROM {self.deleted_table} WHERE id = ?", (id,))
            conn.commit()
            conn.close()
            return True

    def update_directory(self, id, fields, new_values):
        """
        Update user with new user dict
        Recieves a dict returns nothing
        Removing user and adding the updated one
        (May change in the future for better option)
        """
        if(type(fields) != type([])): fields = [fields]
        if(type(new_values) != type([])): new_values = [new_values]
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        sql = f"UPDATE {self.directories_table} SET "
        for field in fields[:-1]:
            sql += f"{field} = ?, "
        sql += f"{fields[-1]} = ? WHERE id = ?"
        try:
            cursor.execute(sql, tuple(new_values + [id]))
            conn.commit()
        except sqlite3.IntegrityError:
            print("Key values already exist in table")
            conn.close()
        conn.close()

    def get_directory_files(self, parent_id):
        """
        Returns the user
        Gets cred (username or password)
        Returns dict of user
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.files_table} WHERE parent = ?", (parent_id,))
        ans = cursor.fetchall()
        conn.close()
        files = []
        for file in ans:
            files.append(self.row_to_dict_file(file))
        return files

    def get_user_directory_files(self, user_id, parent_id):
        """
        Returns the user
        Gets cred (username or password)
        Returns dict of user
        """
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.files_table} WHERE owner_id = ? and parent = ?", (user_id, parent_id))
        ans = cursor.fetchall()
        conn.close()
        files = []
        for file in ans:
            files.append(self.row_to_dict_file(file))
        return files

    def get_sub_directories(self, parent_id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.directories_table} WHERE parent = ?", (parent_id,))
        ans = cursor.fetchall()
        conn.close()
        directories = []
        for directory in ans:
            directories.append(self.row_to_dict_directory(directory))
        return directories

    def get_all_directories(self):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.directories_table}")
        ans = cursor.fetchall()
        conn.close()
        directories = []
        for directory in ans:
            directories.append(self.row_to_dict_directory(directory))
        return directories

    def get_share_file(self, file_id, user_id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.permissions_table} WHERE file_id = ? and user_id = ?", (file_id, user_id))
        row = cursor.fetchone()
        conn.close()
        return row

    def get_all_share_files(self, user_id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT f.* FROM {self.files_table} f JOIN {self.permissions_table} p ON f.id = p.file_id WHERE p.user_id = ? and p.read = ?", (user_id, "True"))
        ans = cursor.fetchall()
        conn.close()
        files = []
        for file in ans:
            files.append(self.row_to_dict_file(file))
        return files

    def get_all_share_directories(self, user_id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT d.* FROM {self.directories_table} d JOIN {self.permissions_table} p ON d.id = p.file_id WHERE p.user_id = ? and p.read = ?", (user_id, "True"))
        ans = cursor.fetchall()
        conn.close()
        directories = []
        for directory in ans:
            directories.append(self.row_to_dict_directory(directory))
        return directories

    def get_perms(self, id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.permissions_table} WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        return row


    def create_share(self, id, owner_id, file_id, user_id, new_perms):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        sql = f"INSERT INTO {self.permissions_table} (id, file_id, owner_id, user_id, read, write, del, rename, download, share) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"   # Insert all dict values and keys to database
        try:
            cursor.execute(sql, [id, file_id, owner_id, user_id] + new_perms)
            conn.commit()
        except sqlite3.IntegrityError:
            print("Key values already exist in table")
            conn.close()
        conn.close()

    def update_sharing_premissions(self, file_id, user_id, new_perms):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        sql = f"UPDATE {self.permissions_table} set read = ?, write = ?, del = ?, rename = ?, download = ?, share = ? WHERE file_id = ? and user_id = ?"   # Insert all dict values and keys to database
        cursor.execute(sql, new_perms + [file_id, user_id])
        conn.commit()
        conn.close()

    def get_file_perms(self, user_id, file_id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT read, write, del, rename, download, share FROM {self.permissions_table} WHERE user_id = ? and file_id = ?", (user_id, file_id))
        row = cursor.fetchone()
        conn.close()
        return row

    def remove_share(self, user_id, id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {self.permissions_table} WHERE file_id = ? and user_id = ?", (id, user_id))
        conn.commit()
        conn.close()



    def get_directory_contents(self, directory_id):
        """
        Recursively get all files and directories within the given directory.
        
        :param db_conn: The sqlite3 database connection.
        :param directory_id: The ID of the directory to start from.
        :return: A list of tuples (full_path, relative_path), where full_path is the path to the file on disk
                and relative_path is the path to be used within the zip file.
        """
        contents = []
        
        # Get all files in this directory
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT sname, fname FROM {self.files_table} WHERE parent = ?", (directory_id,))
        files = cursor.fetchall()
        
        # Assume files are stored in a folder with their ID as their name
        for file_id, file_name in files:
            full_path = os.path.join(f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}\\server\\cloud", str(file_id))  # Change 'your_file_directory' to the folder containing files
            relative_path = file_name  # This is the name that will appear inside the zip
            contents.append((full_path, relative_path))
        
        # Get all subdirectories
        cursor.execute(f"SELECT id, name FROM {self.directories_table} WHERE parent = ?", (directory_id,))
        subdirectories = cursor.fetchall()
        
        for subdirectory_id, subdirectory_name in subdirectories:
            # Recursively get the contents of the subdirectory
            subdir_contents = self.get_directory_contents(subdirectory_id)
            
            # For each item in the subdirectory, prepend the subdirectory name to the relative path
            for full_path, relative_path in subdir_contents:
                contents.append((full_path, os.path.join(subdirectory_name, relative_path)))
        
        return contents


    def get_deleted_files(self, owner_id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT f.* FROM {self.files_table} f JOIN {self.deleted_table} p ON f.id = p.id WHERE p.owner_id = ?", (owner_id,))
        ans = cursor.fetchall()
        conn.close()
        files = []
        for file in ans:
            try:
                file = self.row_to_dict_file(file)
                file["last_edit"] = self.get_deleted_time(file["id"])[0]
                files.append(file)
            except: continue
        return files

    def get_deleted_directories(self, owner_id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT d.* FROM {self.directories_table} d JOIN {self.deleted_table} p ON d.id = p.id WHERE p.owner_id = ?", (owner_id,))
        ans = cursor.fetchall()
        conn.close()
        directories = []
        for directory in ans:
            directories.append(self.row_to_dict_directory(directory))
        return directories

    def get_deleted(self, id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {self.deleted_table} WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        return row

    def get_deleted_time(self, id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"SELECT time_to_delete FROM {self.deleted_table} WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        return row

    def recover(self, id):
        conn = sqlite3.connect(self.database)
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {self.deleted_table} WHERE id = ?", (id,))
        conn.commit()
        conn.close()