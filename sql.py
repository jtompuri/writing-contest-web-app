"""
Provides functions for contest, entry, review, and class management in the Writing Contest Web App.

This module includes functions for creating, retrieving, updating, and deleting contests and entries,
as well as managing reviews, classes, and contest-related statistics.

Functions:
    get_all_contests(limit=None, offset=None)
    add_contest(title, class_id, short_description, long_description, anonymity, public_reviews, public_results, collection_start, collection_end, review_start, review_end)
    get_contest_by_id(contest_id)
    update_contest(contest_id, title, class_id, short_description, long_description, anonymity, public_reviews, public_results, collection_end, review_end)
    delete_contest(contest_id)
    get_contests_for_entry(limit=None, offset=None)
    get_contests_for_review(limit=None, offset=None)
    get_contests_for_results(limit=None, offset=None)
    get_contest_count()
    create_contest(title, class_id, short_description, long_description, anonymity, public_reviews, public_results, collection_end, review_end, private_key)
    add_entry(contest_id, user_id, entry)
    get_all_entries(limit=None, offset=None, contest_id=None, user_search=None)
    get_entry_by_id(entry_id)
    update_entry(entry_id, contest_id, user_id, content)
    delete_entry(entry_id)
    create_entry(contest_id, user_id, content)
    save_entry(contest_id, user_id, entry)
    entry_exists(contest_id, user_id)
    get_entry_count(contest_id=None, user_search=None)
    get_user_entry_for_contest(contest_id, user_id)
    add_review(entry_id, user_id, points, review)
    get_entries_for_review(contest_id)
    save_review(entry_id, user_id, points)
    get_review_count(contest_id)
    get_user_reviews_for_contest(contest_id, user_id)
    get_all_classes()
    get_class_by_id(class_id)
    get_contest_results(contest_id)
    get_user_entries_with_results(user_id)
    get_entry_contest_count()
    get_review_contest_count()
    get_results_contest_count()
"""

import db

# -------------------------------
# Contest CRUD
# -------------------------------


def get_all_contests(limit=None, offset=None):
    """
    Retrieve all contests from the database, including their class information, ordered by collection end date.

    Args:
        limit (int, optional): Maximum number of contests to return.
        offset (int, optional): Number of contests to skip before starting to return results.

    Returns:
        list: A list of contests.
    """
    query = """
        SELECT contests.id, contests.title, contests.collection_end,
               contests.review_end, classes.value AS class_value
        FROM contests
        JOIN classes ON contests.class_id = classes.id
        ORDER BY contests.collection_end DESC
    """
    params = []
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    if offset is not None:
        query += " OFFSET ?"
        params.append(offset)
    return db.query(query, params)


def add_contest(title, class_id, short_description, long_description,
                anonymity, public_reviews, public_results, collection_start,
                collection_end, review_start, review_end):
    """
    Add a new contest to the database with the specified details.

    Args:
        title (str): The title of the contest.
        class_id (int): The ID of the class associated with the contest.
        short_description (str): A short description of the contest.
        long_description (str): A detailed description of the contest.
        anonymity (bool): Whether the contest is anonymous.
        public_reviews (bool): Whether reviews are public.
        public_results (bool): Whether results are public.
        collection_start (str): The start date for collection.
        collection_end (str): The end date for collection.
        review_start (str): The start date for review.
        review_end (str): The end date for review.

    Returns:
        None
    """
    query = """INSERT INTO contests (title, class_id, short_description,
                long_description, anonymity, public_reviews,
                public_results, collection_end, review_end)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
    db.execute(query, [title, class_id, short_description, long_description,
                       anonymity, public_reviews, public_results,
                       collection_end, review_end])


def get_contest_by_id(contest_id):
    """
    Retrieve a contest by its ID.

    Args:
        contest_id (int): The ID of the contest.

    Returns:
        dict or None: The contest details if found, otherwise None.
    """
    query = """
            SELECT contests.id, contests.title, contests.class_id, contests.short_description,
                   contests.long_description, contests.collection_end,
                   contests.review_end, contests.public_reviews,
                   contests.public_results, contests.anonymity,
                   contests.private_key,
                   classes.value AS class_value
            FROM contests
            JOIN classes ON contests.class_id = classes.id
            WHERE contests.id = ?
        """
    result = db.query(query, [contest_id])
    return result[0] if result else None


def update_contest(contest_id, title, class_id, short_description,
                   long_description, anonymity, public_reviews, public_results,
                   collection_end, review_end):
    """
    Update an existing contest with new details.

    Args:
        contest_id (int): The ID of the contest to update.
        title (str): The new title of the contest.
        class_id (int): The new class ID associated with the contest.
        short_description (str): The new short description of the contest.
        long_description (str): The new detailed description of the contest.
        anonymity (bool): Whether the contest is anonymous.
        public_reviews (bool): Whether reviews are public.
        public_results (bool): Whether results are public.
        collection_end (str): The new end date for collection.
        review_end (str): The new end date for review.

    Returns:
        None
    """
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


def delete_contest(contest_id):
    """
    Delete a contest by its ID.

    Args:
        contest_id (int): The ID of the contest to delete.

    Returns:
        None
    """
    query = "DELETE FROM contests WHERE id = ?"
    db.execute(query, [contest_id])


def get_contests_for_entry(limit=None, offset=None):
    """
    Retrieve contests available for entry, ordered by collection end date.

    Args:
        limit (int, optional): Maximum number of contests to return.
        offset (int, optional): Number of contests to skip before starting to return results.

    Returns:
        list: A list of contests available for entry.
    """
    query = """SELECT contests.id, contests.title, contests.short_description,
            contests.collection_end, contests.review_end, classes.value AS class_value,
            contests.anonymity AS anonymity, contests.public_reviews AS public_reviews,
            contests.public_results AS public_results
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
    """
    Retrieve contests available for review, ordered by collection end date.

    Args:
        limit (int, optional): Maximum number of contests to return.
        offset (int, optional): Number of contests to skip before starting to return results.

    Returns:
        list: A list of contests available for review.
    """
    query = """SELECT contests.id, contests.title, contests.short_description,
    contests.collection_end, contests.review_end, classes.value AS class_value,
    contests.anonymity AS anonymity, contests.public_reviews AS public_reviews,
    contests.public_results AS public_results
            FROM contests
            JOIN classes ON contests.class_id = classes.id
            WHERE contests.review_end >= DATE('now')
                AND contests.collection_end < DATE('now')
                AND contests.public_reviews = 1
            ORDER BY contests.collection_end"""
    if limit is not None:
        query += " LIMIT " + str(limit)
    if offset is not None:
        query += " OFFSET " + str(offset)
    return db.query(query)


def get_contests_for_results(limit=None, offset=None):
    """
    Retrieve contests with results available, ordered by collection end date.

    Args:
        limit (int, optional): Maximum number of contests to return.
        offset (int, optional): Number of contests to skip before starting to return results.

    Returns:
        list: A list of contests with results available.
    """
    query = """SELECT contests.id, contests.title, contests.short_description,
    contests.collection_end, contests.review_end, classes.value AS class_value,
    contests.anonymity AS anonymity, contests.public_reviews AS public_reviews,
    contests.public_results AS public_results
            FROM contests
            JOIN classes ON contests.class_id = classes.id
            WHERE contests.review_end < DATE('now')
                AND contests.public_results = 1
            ORDER BY contests.collection_end"""
    if limit is not None:
        query += " LIMIT " + str(limit)
    if offset is not None:
        query += " OFFSET " + str(offset)
    return db.query(query)


def get_contest_count():
    """
    Retrieve the total number of contests.

    Returns:
        int: The total number of contests.
    """
    result = db.query("SELECT COUNT(*) FROM contests")
    return result[0][0]


def create_contest(title, class_id, short_description, long_description,
                   anonymity, public_reviews, public_results,
                   collection_end, review_end, private_key):
    """
    Create a new contest with the specified details.

    Args:
        title (str): The title of the contest.
        class_id (int): The ID of the class associated with the contest.
        short_description (str): A short description of the contest.
        long_description (str): A detailed description of the contest.
        anonymity (bool): Whether the contest is anonymous.
        public_reviews (bool): Whether reviews are public.
        public_results (bool): Whether results are public.
        collection_end (str): The end date for collection.
        review_end (str): The end date for review.
        private_key (str): The private key for the contest.

    Returns:
        None
    """
    query = """
        INSERT INTO contests
        (title, class_id, short_description, long_description,
         anonymity, public_reviews, public_results,
         collection_end, review_end, private_key)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    db.execute(query, [title, class_id, short_description, long_description,
                       anonymity, public_reviews, public_results,
                       collection_end, review_end, private_key])


# -------------------------------
# Entry CRUD
# -------------------------------

def add_entry(contest_id, user_id, entry):
    """
    Add a new entry to the database for a specific contest and user.

    Args:
        contest_id (int): The ID of the contest.
        user_id (int): The ID of the user submitting the entry.
        entry (str): The content of the entry.

    Returns:
        None
    """
    query = """INSERT INTO entries (contest_id, user_id, entry)
             VALUES (?, ?, ?)"""
    db.execute(query, [contest_id, user_id, entry])


def get_all_entries(limit=None, offset=None, contest_id=None, user_search=None):
    """
    Retrieve all entries from the database, including user and contest information, ordered by creation date.

    Args:
        limit (int, optional): Maximum number of entries to return.
        offset (int, optional): Number of entries to skip before starting to return results.
        contest_id (int, optional): Filter entries by contest ID.
        user_search (str, optional): Filter entries by user name or username.

    Returns:
        list: A list of entries.
    """
    query = """
        SELECT entries.id, contests.title AS contest_title,
               users.name AS author_name, users.username
        FROM entries
        JOIN users ON entries.user_id = users.id
        JOIN contests ON entries.contest_id = contests.id
        WHERE 1=1
    """
    params = []
    if contest_id:
        query += " AND contests.id = ?"
        params.append(contest_id)
    if user_search:
        query += " AND (users.name LIKE ? OR users.username LIKE ?)"
        params.extend([f"%{user_search}%", f"%{user_search}%"])
    query += " ORDER BY entries.id DESC"
    if limit is not None and offset is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    return db.query(query, params)


def get_entry_by_id(entry_id):
    """
    Retrieve an entry by its ID, including user, contest info, total points, contest anonymity, and review_end date.

    Args:
        entry_id (int): The ID of the entry.

    Returns:
        dict or None: The entry details if found, otherwise None.
    """
    query = """
        SELECT entries.id, entries.entry, entries.created,
               users.name AS author_name, users.username, contests.title AS contest_title,
               contests.id AS contest_id, users.id AS user_id,
               contests.anonymity AS anonymity,
               contests.review_end AS review_end,
               classes.value AS class_value,
               IFNULL(SUM(reviews.points), 0) AS points
        FROM entries
        JOIN users ON entries.user_id = users.id
        JOIN contests ON entries.contest_id = contests.id
        JOIN classes ON contests.class_id = classes.id
        LEFT JOIN reviews ON reviews.entry_id = entries.id
        WHERE entries.id = ?
        GROUP BY entries.id
    """
    result = db.query(query, [entry_id])
    return result[0] if result else None


def update_entry(entry_id, contest_id, user_id, content):
    """
    Update an existing entry with new details.

    Args:
        entry_id (int): The ID of the entry to update.
        contest_id (int): The new contest ID associated with the entry.
        user_id (int): The new user ID associated with the entry.
        content (str): The new content of the entry.

    Returns:
        None
    """
    query = """
        UPDATE entries
        SET contest_id = ?, user_id = ?, entry = ?
        WHERE id = ?
    """
    db.execute(query, [contest_id, user_id, content, entry_id])


def delete_entry(entry_id):
    """
    Delete an entry by its ID.

    Args:
        entry_id (int): The ID of the entry to delete.

    Returns:
        None
    """
    query = "DELETE FROM entries WHERE id = ?"
    db.execute(query, [entry_id])


def create_entry(contest_id, user_id, content):
    """
    Create a new entry for a specific contest and user.

    Args:
        contest_id (int): The ID of the contest.
        user_id (int): The ID of the user.
        content (str): The content of the entry.

    Returns:
        None
    """
    query = """
        INSERT INTO entries (contest_id, user_id, entry)
        VALUES (?, ?, ?)
    """
    db.execute(query, [contest_id, user_id, content])


def save_entry(contest_id, user_id, entry):
    """
    Save a new entry to the database for a specific contest and user.

    Args:
        contest_id (int): The ID of the contest.
        user_id (int): The ID of the user.
        entry (str): The content of the entry.

    Returns:
        None
    """
    query = """
        INSERT INTO entries (contest_id, user_id, entry)
        VALUES (?, ?, ?)
    """
    db.execute(query, [contest_id, user_id, entry])


def entry_exists(contest_id, user_id):
    """
    Check if an entry already exists for a specific contest and user.

    Args:
        contest_id (int): The ID of the contest.
        user_id (int): The ID of the user.

    Returns:
        bool: True if entry exists, False otherwise.
    """
    query = """SELECT 1 FROM entries WHERE contest_id = ?
                AND user_id = ? LIMIT 1"""
    result = db.query(query, [contest_id, user_id])
    return bool(result)


def get_entry_count(contest_id=None, user_search=None):
    """
    Retrieve the number of entries, optionally filtered by contest ID.

    Args:
        contest_id (int, optional): Filter entries by contest ID.
        user_search (str, optional): Filter entries by user name or username.

    Returns:
        int: The number of entries.
    """
    query = """
        SELECT COUNT(*) AS count
        FROM entries
        JOIN users ON entries.user_id = users.id
        JOIN contests ON entries.contest_id = contests.id
        WHERE 1=1
    """
    params = []
    if contest_id:
        query += " AND contests.id = ?"
        params.append(contest_id)
    if user_search:
        query += " AND (users.name LIKE ? OR users.username LIKE ?)"
        params.extend([f"%{user_search}%", f"%{user_search}%"])
    result = db.query(query, params)
    return result[0]["count"] if result else 0


def get_user_entry_for_contest(contest_id, user_id):
    """
    Retrieve the user's entry for a specific contest, if it exists.

    Args:
        contest_id (int): The ID of the contest.
        user_id (int): The ID of the user.

    Returns:
        dict or None: The entry if found, otherwise None.
    """
    query = "SELECT id FROM entries WHERE contest_id = ? AND user_id = ? LIMIT 1"
    result = db.query(query, [contest_id, user_id])
    return result[0] if result else None


# -------------------------------
# Review CRUD
# -------------------------------

def add_review(entry_id, user_id, points, review):
    """
    Add a new review to the database for a specific entry.

    Args:
        entry_id (int): The ID of the entry being reviewed.
        user_id (int): The ID of the user submitting the review.
        points (int): The score given in the review.
        review (str): The content of the review.

    Returns:
        None
    """
    query = """INSERT INTO reviews (entry_id, user_id, points, review)
             VALUES (?, ?, ?, ?)"""
    db.execute(query, [entry_id, user_id, points, review])


def get_entries_for_review(contest_id):
    """
    Get all entries for a contest in random order for review.

    Args:
        contest_id (int): The ID of the contest.

    Returns:
        list: A list of entries for review.
    """
    query = """
        SELECT entries.id, users.name AS author_name, entries.entry
        FROM entries
        JOIN users ON entries.user_id = users.id
        WHERE entries.contest_id = ?
        ORDER BY RANDOM()
    """
    return db.query(query, [contest_id])


def save_review(entry_id, user_id, points):
    """
    Insert or update a review for an entry by a user.

    Args:
        entry_id (int): The ID of the entry.
        user_id (int): The ID of the user.
        points (int): The score given in the review.

    Returns:
        None
    """
    query = """
        INSERT INTO reviews (entry_id, user_id, points)
        VALUES (?, ?, ?)
        ON CONFLICT(entry_id, user_id) DO UPDATE SET points=excluded.points
    """
    db.execute(query, [entry_id, user_id, points])


def get_review_count(contest_id):
    """
    Retrieve the number of reviews for a specific contest.

    Args:
        contest_id (int): The ID of the contest.

    Returns:
        int: The number of reviews.
    """
    query = """
        SELECT COUNT(*) FROM reviews
        WHERE entry_id IN (SELECT id FROM entries WHERE contest_id = ?)
    """
    return db.query(query, [contest_id])[0][0]


def get_user_reviews_for_contest(contest_id, user_id):
    """
    Retrieve the reviews and points given by a user for a specific contest.

    Args:
        contest_id (int): The ID of the contest.
        user_id (int): The ID of the user.

    Returns:
        dict: Mapping of entry_id to points given by the user.
    """
    query = """
        SELECT reviews.entry_id, reviews.points
        FROM reviews
        JOIN entries ON reviews.entry_id = entries.id
        WHERE entries.contest_id = ? AND reviews.user_id = ?
    """
    return {row["entry_id"]: row["points"] for row in db.query(query, [contest_id, user_id])}


# -------------------------------
# Class helpers
# -------------------------------

def get_all_classes():
    """
    Retrieve all classes from the database ordered by their value.

    Returns:
        list: A list of classes.
    """
    query = "SELECT id, value FROM classes ORDER BY value"
    return db.query(query)


def get_class_by_id(class_id):
    """
    Retrieve a class by its ID.

    Args:
        class_id (int): The ID of the class.

    Returns:
        dict or None: The class details if found, otherwise None.
    """
    query = "SELECT value FROM classes WHERE id = ?"
    result = db.query(query, [class_id])
    return result[0] if result else None


# -------------------------------
# Results, stats, etc.
# -------------------------------

def get_contest_results(contest_id):
    """
    Retrieve all entries for a contest with author name, username, entry text,
    and total review points, ordered by points descending.

    Args:
        contest_id (int): The ID of the contest.

    Returns:
        list: Each dict contains id, author_name, username, entry, points.
    """
    query = """
        SELECT
            entries.id AS id,
            users.name AS author_name,
            users.username AS username,
            entries.entry AS entry,
            IFNULL(SUM(reviews.points), 0) AS points
        FROM entries
        JOIN users ON entries.user_id = users.id
        LEFT JOIN reviews ON reviews.entry_id = entries.id
        WHERE entries.contest_id = ?
        GROUP BY entries.id
        ORDER BY points DESC, entries.id ASC
    """
    return db.query(query, [contest_id])


def get_user_entries_with_results(user_id):
    """
    Retrieve all entries submitted by a user, including contest info, points, placement, and total entries.

    Args:
        user_id (int): The ID of the user.

    Returns:
        list: Each dict contains entry and contest details, points, placement, and total_entries.
    """
    query = """
    SELECT
        entry_id,
        entry_text,
        title,
        anonymity,
        public_reviews,
        public_results,
        collection_end,
        review_end,
        contest_id,
        class_value,
        points,
        placement,
        total_entries,
        user_id
    FROM (
        SELECT
            e.id AS entry_id,
            e.entry AS entry_text,
            c.title AS title,
            c.anonymity,
            c.public_reviews,
            c.public_results,
            c.collection_end,
            c.review_end,
            c.id AS contest_id,
            cl.value AS class_value,
            IFNULL(SUM(r.points), 0) AS points,
            RANK() OVER (
                PARTITION BY e.contest_id
                ORDER BY IFNULL(SUM(r.points), 0) DESC, e.id ASC
            ) AS placement,
            COUNT(*) OVER (PARTITION BY e.contest_id) AS total_entries,
            e.user_id
        FROM entries e
        JOIN contests c ON e.contest_id = c.id
        JOIN classes cl ON c.class_id = cl.id
        LEFT JOIN reviews r ON r.entry_id = e.id
        GROUP BY e.id
    ) AS ranked_entries
    WHERE user_id = ?
    ORDER BY review_end DESC
    """
    return db.query(query, [user_id])


def get_entry_contest_count():
    """
    Retrieve the count of contests available for entry.

    Returns:
        int: The number of contests available for entry.
    """
    query = """
        SELECT COUNT(*) FROM contests
        WHERE collection_end >= DATE('now')
    """
    result = db.query(query)
    return result[0][0] if result else 0


def get_review_contest_count():
    """
    Retrieve the count of contests available for review.

    Returns:
        int: The number of contests available for review.
    """
    query = """
        SELECT COUNT(*) FROM contests
        WHERE review_end >= DATE('now')
          AND collection_end <= DATE('now')
          AND public_reviews = 1
    """
    result = db.query(query)
    return result[0][0] if result else 0


def get_results_contest_count():
    """
    Retrieve the count of contests with results available.

    Returns:
        int: The number of contests with results available.
    """
    query = """
        SELECT COUNT(*) FROM contests
        WHERE review_end < DATE('now')
          AND public_results = 1
    """
    result = db.query(query)
    return result[0][0] if result else 0
