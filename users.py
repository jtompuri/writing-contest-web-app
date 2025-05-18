from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import db

def get_user(user_id):
    sql = "SELECT id, name, username, super_user FROM users WHERE id = ?"
    result = db.query(sql, [user_id])
    return result[0] if result else None


def get_all_users():
    query = """
        SELECT id, name, username, super_user, created
        FROM users
        ORDER BY id ASC
    """
    return db.query(query)


def get_user_count():
    query = "SELECT COUNT(*) FROM users"
    result = db.query(query)
    return result[0][0]


def get_entries(user_id):
    sql = "SELECT id, contest_id, entry FROM entries WHERE user_id = ? ORDER BY id DESC"
    return db.query(sql, [user_id])


def create_user(name, username, password, is_super):
    password_hash = generate_password_hash(password)
    query = "INSERT INTO users (name, username, password_hash, super_user) VALUES (?, ?, ?, ?)"
    try:
        db.execute(query, [name, username, password_hash, is_super])
        return True
    except sqlite3.IntegrityError:
        return False


def update_user(user_id, name, username, is_super):
    query = "UPDATE users SET name = ?, username = ?, super_user = ? WHERE id = ?"
    db.execute(query, [name, username, is_super, user_id])


def delete_user(user_id):
    query = "DELETE FROM users WHERE id = ?"
    db.execute(query, [user_id])


def is_super_user(user_id):
    query = "SELECT super_user FROM users WHERE id = ?"
    result = db.query(query, [user_id])
    return result[0]["super_user"] == 1 if result else False


def get_super_user_count():
    query = "SELECT COUNT(*) FROM users WHERE super_user = 1"
    result = db.query(query)
    return result[0][0] if result else 0


def check_login(username, password):
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
    password_hash = generate_password_hash(password)
    query = "UPDATE users SET password_hash = ? WHERE id = ?"
    db.execute(query, [password_hash, user_id])