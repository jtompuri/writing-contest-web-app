DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS entries;
DROP TABLE IF EXISTS contests;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS classes;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
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
    collection_end DATE,
    review_end DATE,
    private_key TEXT,
    created DATETIME DEFAULT (DATETIME('now')),
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);

CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    contest_id INTEGER,
    user_id INTEGER,
    entry TEXT,
    created DATETIME DEFAULT (DATETIME('now')),
    FOREIGN KEY (contest_id) REFERENCES contests(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (contest_id, user_id)
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER,
    user_id INTEGER,
    points INTEGER,
    review TEXT,
    created DATETIME DEFAULT (DATETIME('now')),
    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(entry_id, user_id)
);

CREATE TABLE classes (
    id INTEGER PRIMARY KEY,
    title TEXT,
    value TEXT
);

INSERT INTO classes VALUES(1,'Runo','Runo');
INSERT INTO classes VALUES(2,'Aforismi','Aforismi');
INSERT INTO classes VALUES(3,'Essee','Essee');

-- Indexes for performance. Comment out when benchmarking indexes.
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_entries_contest_user ON entries(contest_id, user_id);
CREATE INDEX IF NOT EXISTS idx_entries_user_id ON entries(user_id);
CREATE INDEX IF NOT EXISTS idx_entries_contest_id ON entries(contest_id);
CREATE INDEX IF NOT EXISTS idx_reviews_entry_id ON reviews(entry_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_contests_class_id ON contests(class_id);