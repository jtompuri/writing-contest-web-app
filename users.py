"""
users.py

This module provides functions for user management, including user creation,
retrieval, updating, deletion, authentication, and privilege checks for the
Writing Contest Web App.
"""

from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import db


def get_user(user_id):
    """
    Retrieve a user by their ID.

    Args:
        user_id (int): The ID of the user.

    Returns:
        dict or None: User data if found, otherwise None.
    """
    sql = "SELECT id, name, username, super_user FROM users WHERE id = ?"
    result = db.query(sql, [user_id])
    return result[0] if result else None


def get_user_count():
    """
    Retrieve the total number of users.

    Returns:
        int: The total number of users.
    """
    result = db.query("SELECT COUNT(*) FROM users")
    return result[0][0] if result else 0


def get_all_users(limit=None, offset=None):
    """
    Retrieve all users from the database, ordered by their ID.

    Args:
        limit (int, optional): The maximum number of users to return.
        offset (int, optional): The number of users to skip before starting to
                                return results.

    Returns:
        list: A list of users.
    """
    query = "SELECT id, name, username, super_user FROM users ORDER BY id"
    params = []
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    if offset is not None:
        query += " OFFSET ?"
        params.append(offset)
    return db.query(query, params)


def get_entries(user_id):
    """
    Retrieve all entries for a given user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        list: A list of entries for the user.
    """
    sql = """SELECT id, contest_id, entry FROM entries WHERE user_id = ?
            ORDER BY id DESC"""
    return db.query(sql, [user_id])


def create_user(name, username, password, is_super):
    """
    Create a new user.

    Args:
        name (str): The user's name.
        username (str): The user's username.
        password (str): The user's password (plain text).
        is_super (bool or int): Whether the user is a super user.

    Returns:
        bool: True if user was created, False if username already exists.
    """
    password_hash = generate_password_hash(password)
    query = """INSERT INTO users (name, username, password_hash, super_user)
                VALUES (?, ?, ?, ?)"""
    try:
        db.execute(query, [name, username, password_hash, is_super])
        return True
    except sqlite3.IntegrityError:
        return False


def update_user(user_id, name, username, is_super):
    """
    Update user information.

    Args:
        user_id (int): The ID of the user.
        name (str): The new name.
        username (str): The new username.
        is_super (bool or int): Whether the user is a super user.
    """
    query = """UPDATE users SET name = ?, username = ?, super_user = ?
                WHERE id = ?"""
    db.execute(query, [name, username, is_super, user_id])


def delete_user(user_id):
    """
    Delete a user by their ID.

    Args:
        user_id (int): The ID of the user to delete.
    """
    query = "DELETE FROM users WHERE id = ?"
    db.execute(query, [user_id])


def is_super_user(user_id):
    """
    Check if a user is a super user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        bool: True if the user is a super user, False otherwise.
    """
    query = "SELECT super_user FROM users WHERE id = ?"
    result = db.query(query, [user_id])
    return result[0]["super_user"] == 1 if result else False


def get_super_user_count():
    """
    Retrieve the total number of super users.

    Returns:
        int: The number of super users.
    """
    query = "SELECT COUNT(*) FROM users WHERE super_user = 1"
    result = db.query(query)
    return result[0][0] if result else 0


def check_login(username, password):
    """
    Check user credentials for login.

    Args:
        username (str): The username.
        password (str): The password (plain text).

    Returns:
        int or None: The user ID if credentials are correct, otherwise None.
    """
    sql = "SELECT id, password_hash FROM users WHERE username = ?"
    result = db.query(sql, [username])
    if not result:
        return None

    user_id = result[0]["id"]
    password_hash = result[0]["password_hash"]
    if check_password_hash(password_hash, password):
        return user_id
    else:
        return None


def update_password(user_id, password):
    """
    Update a user's password.

    Args:
        user_id (int): The ID of the user.
        password (str): The new password (plain text).
    """
    password_hash = generate_password_hash(password)
    query = "UPDATE users SET password_hash = ? WHERE id = ?"
    db.execute(query, [password_hash, user_id])
