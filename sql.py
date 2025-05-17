
import db

def get_all_classes():
    sql = "SELECT title, value FROM classes ORDER BY id"
    result = db.query(sql)

    classes = {}
    for title, value in result:
        classes[title] = []
    for title, value in result:
        classes[title].append(value)

    return classes

def add_contest(title, class_id, short_description, long_description, anonymity, public_reviews, 
                public_results, collection_start, collection_end, review_start, review_end):
    sql = """INSERT INTO contests (title, class_id, short_description, long_description, anonymity, public_reviews, 
                public_results, collection_end, review_end)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
    db.execute(sql, [title, class_id, short_description, long_description, anonymity, public_reviews, 
                public_results, collection_end, review_end])

def add_entry(title, contest_id, user_id, entry):
    sql = """INSERT INTO entries (title, contest_id, user_id, entry)
             VALUES (?, ?, ?, ?)"""
    db.execute(sql, [title, contest_id, user_id, entry])

def add_review(entry_id, user_id, points, review):
    sql = """INSERT INTO reviws (entry_id, user_id, points, review)
             VALUES (?, ?, ?)"""
    db.execute(sql, [entry_id, user_id, points, review])

def get_active_contests_list():
    sql = """SELECT contests.title, contests.short_description, contests.collection_end, contests.review_end, classes.value
            FROM contests
            JOIN classes ON contests.class_id = classes.id
            WHERE contests.collection_end >= DATE('now')
            ORDER BY contests.collection_end"""
    return db.query(sql)


def get_past_contests_list():
    sql = """SELECT contests.title, contests.short_description, contests.collection_end, contests.review_end, classes.value
            FROM contests
            JOIN classes ON contests.class_id = classes.id
            WHERE contests.review_end > DATE('now')
            ORDER BY contests.collection_end"""
    return db.query(sql)


##### KESKEN: jäin tähän #####


def get_minimum_bid(item_id):
    sql = "SELECT start_price FROM items WHERE id = ?"
    minimum_bid = int(db.query(sql, [item_id])[0][0])

    sql = "SELECT MAX(price) FROM bids WHERE item_id = ?"
    max_price = db.query(sql, [item_id])[0][0]
    if max_price:
        minimum_bid = max_price + 1

    return minimum_bid

def get_classes(item_id):
    sql = "SELECT title, value FROM item_classes WHERE item_id = ?"
    return db.query(sql, [item_id])

def get_items():
    sql = """SELECT items.id, items.title, users.id user_id, users.username,
                    COUNT(bids.id) bid_count
             FROM items JOIN users ON items.user_id = users.id
                        LEFT JOIN bids ON items.id = bids.item_id
             GROUP BY items.id
             ORDER BY items.id DESC"""
    return db.query(sql)

def get_item(item_id):
    sql = """SELECT items.id,
                    items.title,
                    items.description,
                    items.start_price,
                    users.id user_id,
                    users.username
             FROM items, users
             WHERE items.user_id = users.id AND
                   items.id = ?"""
    result = db.query(sql, [item_id])
    return result[0] if result else None

def update_item(item_id, title, description, classes):
    sql = """UPDATE items SET title = ?,
                              description = ?
                          WHERE id = ?"""
    db.execute(sql, [title, description, item_id])

    sql = "DELETE FROM item_classes WHERE item_id = ?"
    db.execute(sql, [item_id])

    sql = "INSERT INTO item_classes (item_id, title, value) VALUES (?, ?, ?)"
    for class_title, class_value in classes:
        db.execute(sql, [item_id, class_title, class_value])

def remove_item(item_id):
    sql = "DELETE FROM bids WHERE item_id = ?"
    db.execute(sql, [item_id])
    sql = "DELETE FROM images WHERE item_id = ?"
    db.execute(sql, [item_id])
    sql = "DELETE FROM item_classes WHERE item_id = ?"
    db.execute(sql, [item_id])
    sql = "DELETE FROM items WHERE id = ?"
    db.execute(sql, [item_id])

def find_items(query):
    sql = """SELECT id, title
             FROM items
             WHERE title LIKE ? OR description LIKE ?
             ORDER BY id DESC"""
    like = "%" + query + "%"
    return db.query(sql, [like, like])
