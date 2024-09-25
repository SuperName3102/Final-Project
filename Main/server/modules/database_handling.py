# 2024 © Idan Hazay

# Import libraries
import os
import sqlite3


# Announce global vars
database = f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}\\server\\database\\database.db"
users_table = "Users"
files_table = "Files"
permissions_table = "Permissions"

def create_tables():
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    #cursor.execute(f"DROP TABLE users")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {users_table} (id TEXT PRIMARY KEY, email TEXT UNIQUE, username TEXT UNIQUE, password TEXT, salt TEXT, last_code INTEGER, valid_until TEXT, verified BOOL, subscription_level INT, admin_level INT)")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {files_table} (id TEXT PRIMARY KEY, sname TEXT UNIQUE, fname TEXT, path TEXT, owner_id TEXT)")
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {permissions_table} (id TEXT PRIMARY KEY, file_id TEXT, user_id TEXT, read BOOL, write BOOL, del BOOL, rename BOOL, download BOOL, share BOOL)")
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
        print("Key values already exist in table")
    conn.close()

def remove_user(cred):
    """
    Removing user from database
    Recieves a cred (username or password)
    Returns nothing
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {users_table} WHERE username = ? or email = ? or id = ?", (cred, cred, cred))
    conn.commit()
    conn.close()

def update_user(cred, user_dict):
    """
    Update user with new user dict
    Recieves a dict returns nothing
    Removing user and adding the updated one
    (May change in the future for better option)
    """
    remove_user(cred)
    add_user(user_dict)


def row_to_dict(row):
    """
    Gets a row of table and returns a dict with that row
    """
    user_dict = {"id": row[0], "email": row[1], "username": row[2], "password": row[3],"salt": row[4],"last_code": row[5],"valid_until": row[6],"verified": bool(row[7]), "subscription_level": int(row[8]), "admin_level": int(row[9])}
    return user_dict

def get_user(cred):
    """
    Returns the user
    Gets cred (username or password)
    Returns dict of user
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {users_table} WHERE username = ? or email = ? or id = ?", (cred, cred, cred))
    row = cursor.fetchone()
    conn.close()
    if row == None: return None
    return row_to_dict(row)







