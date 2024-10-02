# 2024 © Idan Hazay

# Import libraries
import os
import sqlite3
from datetime import datetime
import traceback

# Announce global vars
database = f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}\\server\\database\\database.db"
users_table = "Users"
files_table = "Files"
permissions_table = "Permissions"
directories_table = "Directories"

def create_tables():
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    #cursor.execute(f"DROP TABLE {users_table}")
    #cursor.execute(f"DROP TABLE {files_table}")
    #cursor.execute(f"DROP TABLE {directories_table}")
    cursor.execute(f"DROP TABLE {permissions_table}")
    #cursor.execute(f"CREATE TABLE IF NOT EXISTS {users_table} (id TEXT PRIMARY KEY, email TEXT UNIQUE, username TEXT UNIQUE, password TEXT, salt TEXT, last_code INTEGER, valid_until TEXT, verified BOOL, subscription_level INT, admin_level INT, cookie TEXT UNIQUE, cookie_expiration TEXT)")
    #cursor.execute(f"CREATE TABLE IF NOT EXISTS {files_table} (id TEXT PRIMARY KEY, sname TEXT UNIQUE, fname TEXT, parent TEXT, owner_id TEXT, size TEXT, last_edit TEXT)")
    #cursor.execute(f"CREATE TABLE IF NOT EXISTS {directories_table} (id TEXT PRIMARY KEY, name TEXT, parent TEXT, owner_id TEXT)")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {permissions_table} (id TEXT PRIMARY KEY,  file_id TEXT, owner_id TEXT, user_id TEXT, read BOOL, write BOOL, del BOOL, rename BOOL, download BOOL, share BOOL)")
    conn.commit()
    conn.close()

def get_user_id(cred):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM {users_table} WHERE username = ? or email = ?", (cred, cred))
    row = cursor.fetchone()
    conn.close()
    if row == None: return None
    return row[0]


def add_user(user_dict):
    """
    Adding user to database
    Gets dict returns nothing
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    columns = ', '.join(user_dict.keys())
    values = ', '.join(['?'] * len(user_dict))
    sql = f"INSERT INTO {users_table} ({columns}) VALUES ({values})"   # Insert all dict values and keys to database
    try:
        cursor.execute(sql, list(user_dict.values()))
        conn.commit()
    except sqlite3.IntegrityError:
        print(traceback.format_exc())
        print("Key values already exist in table")
    conn.close()

def remove_user(id):
    """
    Removing user from database
    Recieves a cred (username or password)
    Returns nothing
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {users_table} WHERE id = ?", (id,))
    cursor.execute(f"DELETE FROM {files_table} WHERE owner_id = ?", (id,))
    cursor.execute(f"DELETE FROM {directories_table} WHERE owner_id = ?", (id,))
    cursor.execute(f"DELETE FROM {permissions_table} WHERE owner_id = ?", (id,))
    conn.commit()
    conn.close()



def update_user(id, fields, new_values):
    """
    Update user with new user dict
    Recieves a dict returns nothing
    Removing user and adding the updated one
    (May change in the future for better option)
    """
    if(type(fields) != type([])): fields = [fields]
    if(type(new_values) != type([])): new_values = [new_values]
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    sql = f"UPDATE {users_table} SET "
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

def get_user_values(id, fields):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    sql = f"SELECT "
    for field in fields[:-1]:
        sql += f"{field}, "
    sql += f"{fields[-1]} "
    sql += f"FROM {users_table} WHERE id = ?"
    cursor.execute(sql, (id,))
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return row


def row_to_dict_user(row):
    """
    Gets a row of table and returns a dict with that row
    """
    user_dict = {"id": row[0], "email": row[1], "username": row[2], "password": row[3],"salt": row[4],"last_code": row[5],"valid_until": row[6],"verified": bool(row[7]), "subscription_level": int(row[8]), "admin_level": int(row[9]), "cookie": row[10], "cookie_expiration": row[11]}
    return user_dict

def row_to_dict_file(row):
    """
    Gets a row of table and returns a dict with that row
    """
    file_dict = {"id": row[0], "sname": row[1], "fname": row[2], "parent": row[3], "owner_id": row[4], "size": row[5], "last_edit": row[6]}
    return file_dict

def row_to_dict_directory(row):
    """
    Gets a row of table and returns a dict with that row
    """
    directory_dict = {"id": row[0], "name": row[1], "parent": row[2], "owner_id": row[3]}
    return directory_dict

def get_user(cred):
    """
    Returns the user
    Gets cred (username or password)
    Returns dict of user
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {users_table} WHERE username = ? or email = ? or id = ? or cookie = ?", (cred, cred, cred, cred))
    row = cursor.fetchone()
    conn.close()
    if row == None: return None
    return row_to_dict_user(row)


def update_file(id, fields, new_values):
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
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    sql = f"UPDATE {files_table} SET "
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

def get_file(cred):
    """
    Returns the user
    Gets cred (username or password)
    Returns dict of user
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {files_table} WHERE id = ? or sname = ?", (cred, cred))
    row = cursor.fetchone()
    conn.close()
    if row == None: return None
    return row_to_dict_file(row)

def get_user_files(owner_id):
    """
    Returns the user
    Gets cred (username or password)
    Returns dict of user
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {files_table} WHERE owner_id = ?", (owner_id,))
    ans = cursor.fetchall()
    conn.close()
    files = []
    for file in ans:
        files.append(row_to_dict_file(file))
    return files


def get_files(parent):
    """
    Returns the user
    Gets cred (username or password)
    Returns dict of user
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {files_table} WHERE parent = ?", (parent,))
    ans = cursor.fetchall()
    conn.close()
    files = []
    for file in ans:
        files.append(row_to_dict_file(file))
    return files

def add_file(file_dict):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    columns = ', '.join(file_dict.keys())
    values = ', '.join(['?'] * len(file_dict))
    sql = f"INSERT INTO {files_table} ({columns}) VALUES ({values})"   # Insert all dict values and keys to database
    try:
        cursor.execute(sql, list(file_dict.values()))
        conn.commit()
    except sqlite3.IntegrityError:
        print("Key values already exist in table")
        conn.close()
    conn.close()
    
def delete_file(id):
    """
    Removing user from database
    Recieves a cred (username or password)
    Returns nothing
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {files_table} WHERE id = ?", (id,))
    cursor.execute(f"DELETE FROM {permissions_table} WHERE file_id = ?", (id,))
    conn.commit()
    conn.close()

def get_all_files():
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {files_table}")
    ans = cursor.fetchall()
    conn.close()
    files = []
    for file in ans:
        files.append(row_to_dict_file(file))
    return files

def add_directory(directory_dict):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    columns = ', '.join(directory_dict.keys())
    values = ', '.join(['?'] * len(directory_dict))
    sql = f"INSERT INTO {directories_table} ({columns}) VALUES ({values})"   # Insert all dict values and keys to database
    try:
        cursor.execute(sql, list(directory_dict.values()))
        conn.commit()
    except sqlite3.IntegrityError:
        print("Key values already exist in table")
        conn.close()
    conn.close()

def get_user_directories(owner_id):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {directories_table} WHERE owner_id = ?", (owner_id,))
    ans = cursor.fetchall()
    conn.close()
    directories = []
    for directory in ans:
        directories.append(row_to_dict_directory(directory))
    return directories

def get_directories(parent):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {directories_table} WHERE parent = ?", (parent,))
    ans = cursor.fetchall()
    conn.close()
    directories = []
    for directory in ans:
        directories.append(row_to_dict_directory(directory))
    return directories

def get_directory(id):
    """
    Returns the user
    Gets cred (username or password)
    Returns dict of user
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {directories_table} WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if row == None: return None
    return row_to_dict_directory(row)

def delete_directory(id):
    """
    Removing user from database
    Recieves a cred (username or password)
    Returns nothing
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {directories_table} WHERE id = ?", (id,))
    cursor.execute(f"DELETE FROM {files_table} WHERE parent = ?", (id,))
    cursor.execute(f"DELETE FROM {permissions_table} WHERE file_id = ?", (id,))
    conn.commit()
    conn.close()

def update_directory(id, fields, new_values):
    """
    Update user with new user dict
    Recieves a dict returns nothing
    Removing user and adding the updated one
    (May change in the future for better option)
    """
    if(type(fields) != type([])): fields = [fields]
    if(type(new_values) != type([])): new_values = [new_values]
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    sql = f"UPDATE {directories_table} SET "
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

def get_directory_files(parent_id):
    """
    Returns the user
    Gets cred (username or password)
    Returns dict of user
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {files_table} WHERE parent = ?", (parent_id,))
    ans = cursor.fetchall()
    conn.close()
    files = []
    for file in ans:
        files.append(row_to_dict_file(file))
    return files

def get_user_directory_files(user_id, parent_id):
    """
    Returns the user
    Gets cred (username or password)
    Returns dict of user
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {files_table} WHERE owner_id = ? and parent = ?", (user_id, parent_id))
    ans = cursor.fetchall()
    conn.close()
    files = []
    for file in ans:
        files.append(row_to_dict_file(file))
    return files

def get_sub_directories(parent_id):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {directories_table} WHERE parent = ?", (parent_id,))
    ans = cursor.fetchall()
    conn.close()
    directories = []
    for directory in ans:
        directories.append(row_to_dict_directory(directory))
    return directories

def get_all_directories():
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {directories_table}")
    ans = cursor.fetchall()
    conn.close()
    directories = []
    for directory in ans:
        directories.append(row_to_dict_directory(directory))
    return directories

def get_share_file(file_id, user_id):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {permissions_table} WHERE file_id = ? and user_id = ?", (file_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return row

def get_all_share_files(user_id):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT f.* FROM {files_table} f JOIN {permissions_table} p ON f.id = p.file_id WHERE p.user_id = ? and p.read = ?", (user_id, "True"))
    ans = cursor.fetchall()
    conn.close()
    files = []
    for file in ans:
        files.append(row_to_dict_file(file))
    return files

def get_all_share_directories(user_id):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT d.* FROM {directories_table} d JOIN {permissions_table} p ON d.id = p.file_id WHERE p.user_id = ? and p.read = ?", (user_id, "True"))
    ans = cursor.fetchall()
    conn.close()
    directories = []
    for directory in ans:
        directories.append(row_to_dict_directory(directory))
    return directories

def get_perms(id):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {permissions_table} WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    return row


def create_share(id, owner_id, file_id, user_id, new_perms):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    sql = f"INSERT INTO {permissions_table} (id, file_id, owner_id, user_id, read, write, del, rename, download, share) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"   # Insert all dict values and keys to database
    try:
        cursor.execute(sql, [id, file_id, owner_id, user_id] + new_perms)
        conn.commit()
    except sqlite3.IntegrityError:
        print("Key values already exist in table")
        conn.close()
    conn.close()

def update_sharing_premissions(file_id, user_id, new_perms):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    sql = f"UPDATE {permissions_table} set read = ?, write = ?, del = ?, rename = ?, download = ?, share = ? WHERE file_id = ? and user_id = ?"   # Insert all dict values and keys to database
    cursor.execute(sql, new_perms + [file_id, user_id])
    conn.commit()
    conn.close()

def get_file_perms(user_id, file_id):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT read, write, del, rename, download, share FROM {permissions_table} WHERE user_id = ? and file_id = ?", (user_id, file_id))
    row = cursor.fetchone()
    conn.close()
    return row

def remove_share(user_id, id):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {permissions_table} WHERE file_id = ? and user_id = ?", (id, user_id))
    conn.commit()
    conn.close()



def get_directory_contents(directory_id):
    """
    Recursively get all files and directories within the given directory.
    
    :param db_conn: The sqlite3 database connection.
    :param directory_id: The ID of the directory to start from.
    :return: A list of tuples (full_path, relative_path), where full_path is the path to the file on disk
             and relative_path is the path to be used within the zip file.
    """
    contents = []
    
    # Get all files in this directory
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT sname, fname FROM {files_table} WHERE parent = ?", (directory_id,))
    files = cursor.fetchall()
    
    # Assume files are stored in a folder with their ID as their name
    for file_id, file_name in files:
        full_path = os.path.join(f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}\\server\\cloud", str(file_id))  # Change 'your_file_directory' to the folder containing files
        relative_path = file_name  # This is the name that will appear inside the zip
        contents.append((full_path, relative_path))
    
    # Get all subdirectories
    cursor.execute(f"SELECT id, name FROM {directories_table} WHERE parent = ?", (directory_id,))
    subdirectories = cursor.fetchall()
    
    for subdirectory_id, subdirectory_name in subdirectories:
        # Recursively get the contents of the subdirectory
        subdir_contents = get_directory_contents(subdirectory_id)
        
        # For each item in the subdirectory, prepend the subdirectory name to the relative path
        for full_path, relative_path in subdir_contents:
            contents.append((full_path, os.path.join(subdirectory_name, relative_path)))
    
    return contents
