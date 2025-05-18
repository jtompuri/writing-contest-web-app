
import db

def get_all_classes():
    query = "SELECT title, value FROM classes ORDER BY id"
    result = db.query(query)

    classes = {}
    for title, value in result:
        classes[title] = []
    for title, value in result:
        classes[title].append(value)

    return classes

def add_contest(title, class_id, short_description, long_description, anonymity, public_reviews, 
                public_results, collection_start, collection_end, review_start, review_end):
    query = """INSERT INTO contests (title, class_id, short_description, long_description, anonymity, public_reviews, 
                public_results, collection_end, review_end)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
    db.execute(query, [title, class_id, short_description, long_description, anonymity, public_reviews, 
                public_results, collection_end, review_end])

def add_entry(title, contest_id, user_id, entry):
    query = """INSERT INTO entries (title, contest_id, user_id, entry)
             VALUES (?, ?, ?, ?)"""
    db.execute(query, [title, contest_id, user_id, entry])

def add_review(entry_id, user_id, points, review):
    query = """INSERT INTO reviws (entry_id, user_id, points, review)
             VALUES (?, ?, ?)"""
    db.execute(query, [entry_id, user_id, points, review])

def get_contests_for_entry(limit=None, offset=None):
    query = """SELECT contests.id, contests.title, contests.short_description,
            contests.collection_end, contests.review_end, classes.value
            FROM contests
            JOIN classes ON contests.class_id = classes.id
            WHERE contests.collection_end >= DATE('now')
            ORDER BY contests.collection_end"""
    if limit is not None:
        query += " LIMIT " + str(limit)
    if offset is not None:
        query += " OFFSET " + str(offset)
    return db.query(query)

def get_contests_for_review(limit=None, offset=None):
    query = """SELECT contests.id, contests.title, contests.short_description, contests.collection_end, contests.review_end, classes.value
            FROM contests
            JOIN classes ON contests.class_id = classes.id
            WHERE contests.review_end >= DATE('now') AND contests.collection_end <= DATE('now') AND contests.public_reviews = 1
            ORDER BY contests.collection_end"""
    if limit is not None:
        query += " LIMIT " + str(limit)
    if offset is not None:
        query += " OFFSET " + str(offset)
    return db.query(query)

def get_contests_for_results(limit=None, offset=None):
    query = """SELECT contests.id, contests.title, contests.short_description, contests.collection_end, contests.review_end, classes.value
            FROM contests
            JOIN classes ON contests.class_id = classes.id
            WHERE contests.review_end < DATE('now') AND contests.public_results = 1
            ORDER BY contests.collection_end"""
    if limit is not None:
        query += " LIMIT " + str(limit)
    if offset is not None:
        query += " OFFSET " + str(offset)
    return db.query(query)

def get_contest_by_id(contest_id):
    query = """
            SELECT contests.id, contests.title, contests.short_description,
                contests.long_description, contests.collection_end, contests.review_end,
                contests.public_reviews, contests.public_results, contests.anonymity,
                classes.value AS class_value
            FROM contests
            JOIN classes ON contests.class_id = classes.id
            WHERE contests.id = ?
        """
    result = db.query(query, [contest_id])
    return result[0] if result else None

def get_entry_count(contest_id):
    query = "SELECT COUNT(*) FROM entries WHERE contest_id = ?"
    return db.query(query, [contest_id])[0][0]

def get_review_count(contest_id):
    query = """
        SELECT COUNT(*) FROM reviews
        WHERE entry_id IN (SELECT id FROM entries WHERE contest_id = ?)
    """
    return db.query(query, [contest_id])[0][0]



##### I HAVE PROGRESSED THIS FAR. BELOW IS COPY OF ORGINAL FILE #####


def get_minimum_bid(item_id):
    query = "SELECT start_price FROM items WHERE id = ?"
    minimum_bid = int(db.query(query, [item_id])[0][0])

    query = "SELECT MAX(price) FROM bids WHERE item_id = ?"
    max_price = db.query(query, [item_id])[0][0]
    if max_price:
        minimum_bid = max_price + 1

    return minimum_bid

def get_classes(item_id):
    query = "SELECT title, value FROM item_classes WHERE item_id = ?"
    return db.query(query, [item_id])

def get_items():
    query = """SELECT items.id, items.title, users.id user_id, users.username,
                    COUNT(bids.id) bid_count
             FROM items JOIN users ON items.user_id = users.id
                        LEFT JOIN bids ON items.id = bids.item_id
             GROUP BY items.id
             ORDER BY items.id DESC"""
    return db.query(query)

def get_item(item_id):
    query = """SELECT items.id,
                    items.title,
                    items.description,
                    items.start_price,
                    users.id user_id,
                    users.username
             FROM items, users
             WHERE items.user_id = users.id AND
                   items.id = ?"""
    result = db.query(query, [item_id])
    return result[0] if result else None

def update_item(item_id, title, description, classes):
    query = """UPDATE items SET title = ?,
                              description = ?
                          WHERE id = ?"""
    db.execute(query, [title, description, item_id])

    query = "DELETE FROM item_classes WHERE item_id = ?"
    db.execute(query, [item_id])

    query = "INSERT INTO item_classes (item_id, title, value) VALUES (?, ?, ?)"
    for class_title, class_value in classes:
        db.execute(query, [item_id, class_title, class_value])

def remove_item(item_id):
    query = "DELETE FROM bids WHERE item_id = ?"
    db.execute(query, [item_id])
    query = "DELETE FROM images WHERE item_id = ?"
    db.execute(query, [item_id])
    query = "DELETE FROM item_classes WHERE item_id = ?"
    db.execute(query, [item_id])
    query = "DELETE FROM items WHERE id = ?"
    db.execute(query, [item_id])

def find_items(query):
    query = """SELECT id, title
             FROM items
             WHERE title LIKE ? OR description LIKE ?
             ORDER BY id DESC"""
    like = "%" + query + "%"
    return db.query(query, [like, like])

