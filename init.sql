DELETE FROM classes;
DELETE FROM users;
DELETE FROM contests;
DELETE FROM entries;
DELETE FROM reviews;

INSERT INTO classes (class, value) VALUES ('Laji', 'Runo');
INSERT INTO classes (class, value) VALUES ('Laji', 'Aforismi');
INSERT INTO classes (class, value) VALUES ('Laji', 'Proosa');

INSERT INTO users (name, username, password_hash, super_user) VALUES
('Administrator', 'admin', 'hash_admin', 1),
('Laura', 'laura', 'hash_laura', 0),
('Salanimi', 'mikko', 'hash_mikko', 0);

INSERT INTO contests (
    title, class_id, short_description, long_description,
    anonymity, public_reviews, public_results,
    collection_end, review_end
) VALUES (
    'Kevään runokilpailu',
    1,
    'Runoja keväästä',
    'Kirjoita runo, joka käsittelee kevään tunnelmia ja muutosta.',
    1,  -- nimettömyys käytössä
    1,  -- julkiset arvostelut sallittu
    1,  -- tulokset julkistetaan
    '2025-04-15',
    '2025-04-30'
),

(
    'Aforismikilpailu',
    2,
    'Aforismikilpailun lyhytkuvaus',
    'Tarjoa kilpailuun aforismeja, joka teemana on juhla.',
    1,  -- nimettömyys käytössä
    1,  -- julkiset arvostelut sallittu
    1,  -- tulokset julkistetaan
    '2025-03-15',
    '2025-03-30'
),

(
    'Proosakilpailu',
    3,
    'Proosakilpailun kuvaus.',
    'Kirjoita lyhyt proosateksti, joka käsittelee kaupungistumista.',
    1,  -- nimettömyys käytössä
    1,  -- julkiset arvostelut sallittu
    1,  -- tulokset julkistetaan
    '2025-05-20',
    '2025-06-30'
);

INSERT INTO entries (contest_id, user_id, entry) VALUES
(1, 2, 'Kevät saapuu varoen, sulaa lumi sanoiksi.'),
(1, 3, 'Ensimmäinen vihreä – ja minä hengitän uudelleen.');

-- Arvostelut
INSERT INTO reviews (entry_id, user_id, points, review) VALUES
(1, 3, 4, 'Kaunis ja herkkä, mutta hieman ennalta-arvattava.'),
(2, 2, 5, 'Vahva mielikuva ja aito tunne kevään alusta.');