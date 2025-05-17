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
    class_id INTEGER,
    short_description TEXT,
    long_description TEXT,
    anonymity BOOLEAN,
    public_reviews BOOLEAN,
    public_results BOOLEAN,
    collection_start DATE,
    collection_end DATE,
    review_start DATE,
    review_end DATE,
    created DATETIME DEFAULT (DATETIME('now')),
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);

CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    contest_id INTEGER,
    user_id INTEGER,
    entry TEXT,
    created DATETIME DEFAULT (DATETIME('now')),
    FOREIGN KEY (contest_id) REFERENCES contests(id) ON DELETE CASCADE
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER,
    user_id INTEGER,
    points INTEGER,
    review TEXT,
    created DATETIME DEFAULT (DATETIME('now')),
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE classes (
    id INTEGER PRIMARY KEY,
    title TEXT,
    value TEXT
);