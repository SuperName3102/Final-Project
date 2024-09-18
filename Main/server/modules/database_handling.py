# 2024 © Idan Hazay
# Import libraries
import os
import sqlite3


# Announce global vars
database = f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}\\server\\database\\users.db"
table_name = "users"

def add_user(user_dict):
    """
    Adding user to database
    Gets dict returns nothing
    """
    check_table()
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    columns = ', '.join(user_dict.keys())
    values = ', '.join(['?'] * len(user_dict))
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"   # Insert all dict values and keys to database
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
    check_table()
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table_name} WHERE username = ? or email = ?", (cred, cred))
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

def check_table():
    """
    Making sure that our users table exists
    If not make one
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (email TEXT PRIMARY KEY, username TEXT UNIQUE, tz TEXT, password TEXT, salt TEXT, last_code INTEGER, valid_until TEXT, verified BOOL, subscription_level INT, admin_level INT)")
    conn.commit()
    conn.close()

def row_to_dict(row):
    """
    Gets a row of table and returns a dict with that row
    """
    user_dict = {"email": row[0], "username": row[1], "password": row[2],"salt": row[3],"last_code": row[4],"valid_until": row[5],"verified": bool(row[6]), "subscription_level": bool(row[7]), "admin_level": bool(row[8])}
    return user_dict

def get_user(cred):
    """
    Returns the user
    Gets cred (username or password)
    Returns dict of user
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (email TEXT PRIMARY KEY, username TEXT UNIQUE, tz TEXT, password TEXT, salt TEXT, last_code INTEGER, valid_until TEXT, verified BOOL, subscription_level INT, admin_level INT)")
    cursor.execute(f"SELECT * FROM {table_name} WHERE username = ? or email = ?", (cred, cred))
    row = cursor.fetchone()
    conn.close()
    if row == None: return None
    return row_to_dict(row)





