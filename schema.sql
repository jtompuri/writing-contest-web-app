DROP TABLE users;
DROP TABLE contests;
DROP TABLE entries;
DROP TABLE reviews;
DROP TABLE classes;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    super_user BOOLEAN,
    created DATETIME DEFAULT (DATETIME('now'))
);

CREATE TABLE contests (
    id INTEGER PRIMARY KEY,
    title TEXT,
    short_description TEXT,
    long_description TEXT,
    anonymity BOOLEAN,
    public_reviews BOOLEAN,
    public_results BOOLEAN,
    collection_start_date DATE,
    collection_end_date DATE,
    review_start_date DATE,
    review_end_date DATE,
    created DATETIME DEFAULT (DATETIME('now'))
);

CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    contest_id INTEGER,
    user_id INTEGER,
    entry TEXT,
    created DATETIME DEFAULT (DATETIME('now')),
    modified DATETIME,
    FOREIGN KEY (contest_id) REFERENCES contests(id) ON DELETE CASCADE
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER,
    user_id INTEGER,
    points INTEGER,
    review TEXT,
    created DATETIME DEFAULT (DATETIME('now')),
    modified DATETIME,
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE classes (
    id INTEGER PRIMARY KEY,
    contest_id INTEGER,
    class TEXT
);