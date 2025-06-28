"""
Automated script to compare SQLite query speed with and without indexes
for the Writing Contest Web App. It will:
1. Recreate the database from schema.sql.
2. Populate it with random data.
3. Time a set of representative queries.
4. Add indexes and repeat the timing.
5. Print a comparison report.
"""

import os
import sqlite3
import time
import random
import string
from datetime import datetime, timedelta
import secrets
from werkzeug.security import generate_password_hash

DATABASE = "database.db"
SCHEMA = "schema.sql"

# --- CONFIGURABLE TEST DATA SIZES ---
USER_COUNT = 30
CONTEST_COUNT = 100
ENTRY_COUNT = 1000
REVIEW_COUNT = 2000
CLASS_COUNT = 3

# --- INDEX DEFINITIONS ---
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
    "CREATE INDEX IF NOT EXISTS idx_entries_contest_user "
    "ON entries(contest_id, user_id);",
    "CREATE INDEX IF NOT EXISTS idx_entries_user_id ON entries(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_entries_contest_id "
    "ON entries(contest_id);",
    "CREATE INDEX IF NOT EXISTS idx_reviews_entry_id ON reviews(entry_id);",
    "CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_contests_class_id ON contests(class_id);"
]

LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
    "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi "
    "ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
    "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
    "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa "
    "qui officia deserunt mollit anim id est laborum."
)


def random_string(length):
    """Generates a random alphanumeric string of a given length.

    Args:
        length (int): The desired length of the string.

    Returns:
        str: The generated random string.
    """
    return "".join(
        random.choices(string.ascii_letters + string.digits, k=length)
    )


def random_lorem(length):
    """Generates a string of lorem ipsum text of a specific length.

    Args:
        length (int): The desired length of the lorem ipsum text.

    Returns:
        str: The generated lorem ipsum string.
    """
    base = (LOREM + " ") * ((length // len(LOREM)) + 1)
    return base[:length]


def random_date(start, end):
    """Generates a random date between two given dates.

    Args:
        start (datetime.date): The start date of the range.
        end (datetime.date): The end date of the range.

    Returns:
        str: The random date formatted as "YYYY-MM-DD".
    """
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime("%Y-%m-%d")


def recreate_db():
    """Remove and recreate the database from schema.sql."""
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    with open(SCHEMA, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn = sqlite3.connect(DATABASE)
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()


def _populate_users(cur):
    """Populate the users table with an admin and random users."""
    # Add admin user
    admin_password_hash = generate_password_hash("admin")
    cur.execute(
        "INSERT INTO users (name, username, password_hash, super_user) "
        "VALUES (?, ?, ?, ?)",
        ("admin", "admin", admin_password_hash, 1)
    )
    # Add random users
    for i in range(USER_COUNT):
        name = f"User {i + 1}"
        username = f"user{i + 1}@example.com"
        password_hash = random_string(60)
        cur.execute(
            "INSERT INTO users (name, username, password_hash, super_user) "
            "VALUES (?, ?, ?, ?)",
            (name, username, password_hash, 0)
        )


def _populate_contests(cur):
    """Populate contests and return the ID of the demo contest."""
    today = datetime.now()
    # --- Ensure at least one contest is in review period ---
    private_key = secrets.token_urlsafe(16)
    collection_end = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    review_end = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    cur.execute(
        "INSERT INTO contests (title, class_id, short_description, "
        "long_description, anonymity, public_reviews, public_results, "
        "collection_end, review_end, private_key) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("Demo Review Contest", 1, "Demo contest with open review period.",
         "This contest is in review period for demo purposes.", 0, 1, 0,
         collection_end, review_end, private_key)
    )
    demo_contest_id = cur.lastrowid

    # Finished and ongoing contests
    finished_count = int(CONTEST_COUNT * 0.3)
    for i in range(CONTEST_COUNT):
        is_finished = i < finished_count
        title = f"Contest {i + 1}"
        if is_finished:
            collection_end_dt = today - timedelta(days=random.randint(30, 365))
            review_end_dt = collection_end_dt + \
                timedelta(days=random.randint(1, 29))
        else:
            collection_end_dt = today + \
                timedelta(days=random.randint(-10, 365))
            review_end_dt = collection_end_dt + \
                timedelta(days=random.randint(1, 365))

        cur.execute(
            "INSERT INTO contests (title, class_id, short_description, "
            "long_description, anonymity, public_reviews, public_results, "
            "collection_end, review_end, private_key) VALUES (?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?)",
            (title, random.randint(1, CLASS_COUNT), random_lorem(100),
             random_lorem(500), random.randint(0, 1), random.randint(0, 1),
             1 if is_finished else random.randint(0, 1),
             collection_end_dt.strftime("%Y-%m-%d"),
             review_end_dt.strftime("%Y-%m-%d"), secrets.token_urlsafe(16))
        )
    return demo_contest_id


def _populate_entries(cur, demo_contest_id):
    """Populate the entries table."""
    entry_pairs = set()
    all_contest_ids = list(range(1, CONTEST_COUNT + 1)) + [demo_contest_id]
    for _ in range(ENTRY_COUNT):
        while True:
            contest_id = random.choice(all_contest_ids)
            user_id = random.randint(1, USER_COUNT)
            if (contest_id, user_id) not in entry_pairs:
                entry_pairs.add((contest_id, user_id))
                break
        entry = random_lorem(random.randint(100, 5000))
        cur.execute(
            "INSERT INTO entries (contest_id, user_id, entry) "
            "VALUES (?, ?, ?)",
            (contest_id, user_id, entry)
        )


def _populate_reviews(cur):
    """Populate the reviews table."""
    review_pairs = set()
    attempts = 0
    cur.execute("SELECT id FROM entries")
    all_entry_ids = [row[0] for row in cur.fetchall()]
    if not all_entry_ids:
        return

    while len(review_pairs) < REVIEW_COUNT and attempts < REVIEW_COUNT * 10:
        entry_id = random.choice(all_entry_ids)
        user_id = random.randint(1, USER_COUNT)
        if (entry_id, user_id) in review_pairs:
            attempts += 1
            continue
        review_pairs.add((entry_id, user_id))
        points = random.randint(1, 10)
        review = random_lorem(random.randint(50, 500))
        cur.execute(
            "INSERT INTO reviews (entry_id, user_id, points, review) "
            "VALUES (?, ?, ?, ?)",
            (entry_id, user_id, points, review)
        )
        attempts += 1


def populate_db():
    """Populate the database with random data."""
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    _populate_users(cur)
    demo_contest_id = _populate_contests(cur)
    _populate_entries(cur, demo_contest_id)
    _populate_reviews(cur)

    conn.commit()
    conn.close()


def add_indexes():
    """Add indexes to the database."""
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    for idx_sql in INDEXES:
        cur.execute(idx_sql)
    conn.commit()
    conn.close()


def time_queries():
    """Run and time a set of representative queries."""
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    timings = {}

    # 1. Search user by username
    username = f"user{random.randint(1, USER_COUNT)}@example.com"
    t0 = time.perf_counter()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    cur.fetchall()
    timings["search_user_by_username"] = time.perf_counter() - t0

    # 2. List entries for a contest
    contest_id = random.randint(1, CONTEST_COUNT)
    t0 = time.perf_counter()
    cur.execute("SELECT * FROM entries WHERE contest_id = ?", (contest_id,))
    cur.fetchall()
    timings["list_entries_for_contest"] = time.perf_counter() - t0

    # 3. List entries for a user
    user_id = random.randint(1, USER_COUNT)
    t0 = time.perf_counter()
    cur.execute("SELECT * FROM entries WHERE user_id = ?", (user_id,))
    cur.fetchall()
    timings["list_entries_for_user"] = time.perf_counter() - t0

    # 4. Search entries by username (join)
    search = f"user{random.randint(1, USER_COUNT)}"
    t0 = time.perf_counter()
    cur.execute(
        "SELECT entries.* FROM entries "
        "JOIN users ON entries.user_id = users.id "
        "WHERE users.username LIKE ?",
        (f"%{search}%",)
    )
    cur.fetchall()
    timings["search_entries_by_username"] = time.perf_counter() - t0

    # 5. List reviews for an entry
    entry_id = random.randint(1, ENTRY_COUNT)
    t0 = time.perf_counter()
    cur.execute("SELECT * FROM reviews WHERE entry_id = ?", (entry_id,))
    cur.fetchall()
    timings["list_reviews_for_entry"] = time.perf_counter() - t0

    # 6. List contests for a class
    class_id = random.randint(1, CLASS_COUNT)
    t0 = time.perf_counter()
    cur.execute("SELECT * FROM contests WHERE class_id = ?", (class_id,))
    cur.fetchall()
    timings["list_contests_for_class"] = time.perf_counter() - t0

    conn.close()
    return timings


def print_report(timings_no_idx, timings_idx):
    """Prints a formatted report comparing query timings.

    Args:
        timings_no_idx (dict): A dictionary of query timings without indexes.
        timings_idx (dict): A dictionary of query timings with indexes.
    """
    print("\n--- Query Timing Comparison ---")
    print(
        f"{'Query':40} | {'No Index (s)':>12} | "
        f"{'With Index (s)':>14} | {'Speedup':>8}"
    )
    print("-" * 80)
    for key in timings_no_idx:
        t1 = timings_no_idx[key]
        t2 = timings_idx[key]
        speedup = (t1 / t2) if t2 > 0 else float("inf")
        print(
            f"{key:40} | {t1:12.6f} | {t2:14.6f} | {speedup:8.2f}x"
        )
    print("-" * 80)


def print_table_counts():
    """Print the number of records in each table."""
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    tables = ["users", "contests", "entries", "reviews", "classes"]
    print("\n--- Table Record Counts ---")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"{table.capitalize():10}: {count}")
    conn.close()


def main():
    """Orchestrates the database seeding and query timing process."""
    print("Step 1: Recreate DB and populate with random data...")
    recreate_db()
    populate_db()
    print_table_counts()
    print("Step 2: Timing queries WITHOUT indexes...")
    timings_no_idx = time_queries()

    print("Step 3: Adding indexes...")
    add_indexes()
    print("Step 4: Timing queries WITH indexes...")
    timings_idx = time_queries()

    print_table_counts()
    print_report(timings_no_idx, timings_idx)


if __name__ == "__main__":
    main()
