
import db
from datetime import datetime

def get_all_classes():
    query = "SELECT id, value FROM classes ORDER BY value"
    return db.query(query)


def get_all_contests():
    query = """
        SELECT contests.id, contests.title, contests.collection_end,
               contests.review_end, classes.value AS class_value
        FROM contests
        JOIN classes ON contests.class_id = classes.id
        ORDER BY contests.collection_end DESC
    """
    return db.query(query)


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


def get_contest_count():
    result = db.query("SELECT COUNT(*) FROM contests")
    return result[0][0]


def delete_contest(contest_id):
    query = "DELETE FROM contests WHERE id = ?"
    db.execute(query, [contest_id])


def get_all_entries():
    query = """
        SELECT entries.id, entries.entry, entries.created,
               users.username, contests.title AS contest_title
        FROM entries
        JOIN users ON entries.user_id = users.id
        JOIN contests ON entries.contest_id = contests.id
        ORDER BY entries.created DESC
    """
    return db.query(query)


def get_entry_count(contest_id=None):
    if contest_id:
        sql = "SELECT COUNT(*) FROM entries WHERE contest_id = ?"
        result = db.query(sql, [contest_id])
    else:
        sql = "SELECT COUNT(*) FROM entries"
        result = db.query(sql)
    return result[0][0]

def get_review_count(contest_id):
    query = """
        SELECT COUNT(*) FROM reviews
        WHERE entry_id IN (SELECT id FROM entries WHERE contest_id = ?)
    """
    return db.query(query, [contest_id])[0][0]


def create_contest(title, class_id, short_description, long_description,
                   anonymity, public_reviews, public_results,
                   collection_end, review_end):
    query = """
        INSERT INTO contests
        (title, class_id, short_description, long_description,
         anonymity, public_reviews, public_results,
         collection_end, review_end)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    db.execute(query, [title, class_id, short_description, long_description,
                       anonymity, public_reviews, public_results,
                       collection_end, review_end])
    

def update_contest(contest_id, title, class_id, short_description, long_description,
                   anonymity, public_reviews, public_results,
                   collection_end, review_end):
    query = """
        UPDATE contests SET
            title = ?,
            class_id = ?,
            short_description = ?,
            long_description = ?,
            anonymity = ?,
            public_reviews = ?,
            public_results = ?,
            collection_end = ?,
            review_end = ?
        WHERE id = ?
    """
    db.execute(query, [title, class_id, short_description, long_description,
                       anonymity, public_reviews, public_results,
                       collection_end, review_end, contest_id])
    

def create_entry(contest_id, user_id, entry_text):
    query = """
        INSERT INTO entries (contest_id, user_id, entry)
        VALUES (?, ?, ?)
    """
    db.execute(query, [contest_id, user_id, entry_text])


def get_class_by_id(class_id):
    query = "SELECT value FROM classes WHERE id = ?"
    result = db.query(query, [class_id])
    return result[0] if result else None


def save_entry(contest_id, user_id, entry):
    query = """
        INSERT INTO entries (contest_id, user_id, entry)
        VALUES (?, ?, ?)
    """
    db.execute(query, [contest_id, user_id, entry])


def entry_exists(contest_id, user_id):
    query = "SELECT 1 FROM entries WHERE contest_id = ? AND user_id = ? LIMIT 1"
    result = db.query(query, [contest_id, user_id])
    return bool(result)


def get_entry_contest_count():
    query = """
        SELECT COUNT(*) FROM contests
        WHERE collection_end >= DATE('now')
    """
    result = db.query(query)
    return result[0][0] if result else 0


def get_review_contest_count():
    query = """
        SELECT COUNT(*) FROM contests
        WHERE review_end >= DATE('now')
          AND collection_end <= DATE('now')
          AND public_reviews = 1
    """
    result = db.query(query)
    return result[0][0] if result else 0


def get_results_contest_count():
    query = """
        SELECT COUNT(*) FROM contests
        WHERE review_end < DATE('now')
          AND public_results = 1
    """
    result = db.query(query)
    return result[0][0] if result else 0