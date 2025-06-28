# Kirjoituskilpailusovellus

Kirjoituskilpailusovelluksen (Writing Contest Web App) avulla voidaan järjestää kirjoituskilpailuja, joissa kerätään ja arvioidaan lyhyitä tekstejä, kuten runoja, aforismeja tai esseitä.

## Sovelluksen asennus

1. Luo virtuaaliympäristö:
	```bash
	python3 -m venv venv
	```

	Linux/Mac:
	```bash
	source venv/bin/activate
	```

	Windows:
	```bash
	venv\Scripts\activate
	```

2. Asenna `flask`-kirjasto:
	```bash
	pip install flask
	```

3. Tarkista, että `sqlite3` on asennetuna:
	```bash
	sqlite3 --version
	```

	Jos `sqlite3` ei löydy, asenna se.

	Linux:
	```bash
	sudo apt install sqlite3
	```

	Mac:
	```bash
	brew install sqlite3
	```

4. Vaihtoehto 1: Luo tietokanta demosisällöllä:
	```bash
	sqlite3 database.db < init.sql
	```

	Vaihtoehto 2: Luo tyhjä tietokanta (vain kirjallisuuslajit luodaan valmiiksi):
	```bash
	sqlite3 database.db < schema.sql
	```

5. Voit käynnistää sovelluksen:
	```bash
	flask run
	```
	tai
	```bash
	flask run --debug
	```

Voit kirjautua demoon pääkäyttäjänä käyttäjätunnuksella `admin` ja salasanalla `admin`. Pääkäyttäjänä voit hallinnoida kilpailuja, käyttäjiä ja kilpailutöitä.

Jos luot tyhjän tietokannan, niin ensimmäisestä rekisteröidystä käyttäjästä tulee automaattisesti pääkäyttäjä, joka voi luoda, muokata ja poistaa käyttäjiä, kilpailuja ja kilpailutöitä.

Kirjautumaton käyttäjä ei näe Arvioi, Tekstisi ja Ylläpito-välilehtiä. Voit luoda toisen käyttäjätunnuksen, jolla on peruskäyttäjän oikeudet. Peruskäyttäjä ei näe Ylläpito-välilehteä.

## Työn eteneminen

Työn etenemistä voi seurata alla olevasta tehtävälistasta.

### Välipalautus 1 (18.5.2025) ✅
- [x] Luo GitHubiin julkinen repositorio harjoitustyötä varten. Nimeä repositoriosi kuvaavasti.
- [x] Valitse projektille aihe ja kirjoita README.md-tiedostoon kuvaus, joka esittelee sovelluksen keskeiset toiminnot.
- [x] Kirjoita kuvaus samassa muodossa kuin aloitussivun esimerkkiaiheissa ja esimerkkisovelluksessa.
- [x] Kirjaudu Labtooliin ja ilmoita siellä projektisi GitHub-osoite.

### Välipalautus 2 (1.6.2025) ✅
- [x] Tavoitteena on, että sovelluksessa on ainakin seuraavat toiminnot:
	- [x] Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
	- [x] Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan tietokohteita.
	- [x] Käyttäjä näkee sovellukseen lisätyt tietokohteet.
	- [x] Käyttäjä pystyy etsimään tietokohteita hakusanalla tai muulla perusteella.
- [x] README.md-tiedoston tulee kuvata, mikä on sovelluksen nykyinen tilanne.

### Välipalautus 3 (15.6.2025) ✅

- [x] Tavoitteena on, että sovelluksessa on ainakin seuraavat toiminnot:
	- [x] Sovelluksessa on käyttäjäsivut, jotka näyttävät tilastoja ja käyttäjän lisäämät tietokohteet.
	- [x] Käyttäjä pystyy valitsemaan tietokohteelle yhden tai useamman luokittelun. Mahdolliset luokat ovat tietokannassa.
	- [x] Käyttäjä pystyy lähettämään toisen käyttäjän tietokohteeseen liittyen jotain lisätietoa, joka tulee näkyviin sovelluksessa.
- [x] README.md-tiedoston tulee kuvata, mikä on sovelluksen nykyinen tilanne.

### Loppupalautus (27.6.2025)

Huomioitavaa kurssityön arvioinnissa:
- Sovelluksen kaikki ominaisuudet on käytettävissä käyttäjätunnuksella `admin` ja salasanalla `admin`
- Arviointia varten on hyvä rekisteröidä myös peruskäyttäjä, jolla ei ole ylläpito-oikeuksia
- Tietokohteiden haku hakusanalla tai suodattamalla on toteutettu ylläpitokäyttöliittymään
- Sovelluksen koodi on jaettu Flask Blueprint -moduuleiksi kansiossa `routes/`
- Demodataan on lisätty kilpailu, jonka arviointijakso päättyy 31.8.2025
- "Tekstisi"-sivu on kurssivaatimusten käyttäjäsivu, josta listaa käyttäjän kilpailutyöt ja näyttää tilastotietona käyttäjän jättämien kilpailutöiden ja arvosteluiden lukumäärän
- Kilpailun asetuksissa valinnat "anonyymi arviointi" ja "julkinen arviointi" ovat erillisiä valintoja (eivät toistensa vastakohtia):
	- anonyymi arviointi tarkoittaa, että kilpailutyön tekijän nimeä ei esitetä arvioijalle
	- julkinen arviointi tarkoittaa, että kaikki käyttäjät voivat arvoida kilpailutöitä; muussa tapauksessa vain salaisen avaimen sisältämän linkin saaneet voivat arvioida kilpailutöitä
- Vertaisarvioinneissa ja kurssin ohjaajien palautteessa ehdotetut seuraavat parannukset on toteutettu:
	- koodin liian pitkät rivit on jaettu useammalle riville
	- pitkäksi kasvanut `app.py` on jaettu pienemmiksi moduuleiksi kansiossa `routes/`
	- sovelluksen asennusohjeisiin on lisätty puuttuneet yksityiskohdat
	- SQL-injektioriski tiedostossa `sql.py` on korjattu käyttämällä parametreja
	- kirjautuneelta käyttäjältä piilotetaan rekisteröitymis- ja kirjautumislinkit
	- demodataan lisätty arvostelu, jolla on pitkä arviointiperiodi, joten se on arvioitavissa
- Koska sovellus kasvoi suhteellisen laajaksi, toteutin sille kattavat yksikkötestit
	- yksikkötestit helpotti merkittävästi muutosten tekemistä sovellukseen
	- yksikkötestit eivät olleet kurssin vaatimuksissa, mutta koin ne hyödyllisiksi
	- testikattavuus on tällä hetkellä 95 %, tarkempi testikattavuusraportti löytyy alta
- Testaus suurilla datamäärillä on tehty ja testien raportit löytyvät alta
- Olen korjannut kaikki `pylint *.py` komennolla löytämäni varoitukset ja virheet

## Toteutetut ominaisuudet

Arvostelusivulla mainitut toteutetut vaatimukset:

### Sovelluksen perusvaatimukset (7 p)
- [x] Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen
- [x] Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan tietokohteita
- [x] Käyttäjä näkee sovellukseen lisätyt tietokohteet
- [x] Käyttäjä pystyy etsimään tietokohteita hakusanalla tai muulla perusteella
- [x] Käyttäjäsivu näyttää tilastoja ja käyttäjän lisäämät tietokohteet
- [x] Käyttäjä pystyy valitsemaan tietokohteelle yhden tai useamman luokittelun
- [x] Käyttäjä pystyy lisäämään tietokohteeseen toissijaisia tietokohteita

### Tekniset perusvaatimukset (8 p)
- [x] Sovellus toteutettu kurssimateriaalin mukaisesti
- [x] Sovellus toteutettu Pythonilla käyttäen Flask-kirjastoa
- [x] Sovellus käyttää SQLite-tietokantaa
- [x] Kehitystyössä käytetty Gitiä ja GitHubia
- [x] Sovelluksen käyttöliittymä muodostuu HTML-sivuista
- [x] Sovelluksessa ei ole käytetty JavaScript-koodia
- [x] Tietokantaa käytetään suoraan SQL-komennoilla (ei ORMia)
- [x] Kirjaston flask lisäksi käytössä ei muita erikseen asennettavia kirjastoja
 
### Toimivuus ja käytettävyys (15 p)
- [x] Käyttäjän yleiskokemus sovelluksen toimivuudesta
- [x] Käyttäjän yleiskokemus sovelluksen käytettävyydestä
- [x] Käyttäjän lähettämässä tekstissä rivinvaihdot näkyvät selaimessa
- [ ] Kuvissa käytetty alt-attribuuttia (jos sovelluksessa kuvia) [sovelluksessa ei ole kuvia]
- [x] Lomakkeissa käytetty label-elementtiä
- [x] CSS:n avulla toteutettu ulkoasu (itse tehty, ei CSS-kirjastoa)

### Versionhallinta (10 p)
- [x] Kehitystyön aikana on tehty commiteja säännöllisesti
- [x] Commit-viestit on kirjoitettu englanniksi
- [x] Commitit ovat hyviä kokonaisuuksia ja niissä on hyvät viestit
- [x] Versionhallinnassa ei ole sinne kuulumattomia tiedostoja
- [x] Tiedosto README.md antaa hyvän kuvan sovelluksesta

### Ohjelmointityyli (15 p)
- [x] Yleiskuva koodin laadusta (selkeys, luettavuus ja tyyli)
- [x] Sisennyksen leveys on neljä välilyöntiä
- [x] Koodi on kirjoitettu englanniksi
- [x] Muuttujien ja funktioiden nimet muotoa total_count (ei totalCount)
- [x] Merkkijonoissa käytetty aina joko ' tai "  
- [x] Välit oikein =-merkin ympärillä
- [x] Välit oikein ,-merkin ympärillä
- [x] Ei koodia tyyliin `if success return True else return False`
- [x] Jos funktio palauttaa arvon, tulee olla useita mahdollisia palautusarvoja
- [x] Ei sulkeita if- ja while-rakenteiden ehtojen ympärillä
- [x] Ei ehtoja tyyliin result == None ja result is None

### Tietokanta-asiat (15 p)
- [x] Taulut ja sarakkeet on nimetty englanniksi
- [x] Taulut ja sarakkeet on nimetty hyvin
- [x] Käytetty REFERENCES-määrettä, kun viittaus toiseen tauluun
- [x] Käytetty UNIQUE-määrettä, kun tulee olla eri arvo joka rivillä
- [x] Ei kyselyjä muotoa SELECT *
- [x] Pitkät SQL-komennot jaettu usealle riville
- [x] Kaikki tiedot haetaan yhdellä SQL-kyselyllä, jos järkevästi mahdollista
- [x] Koodissa ei tehdä asioita, jotka voi mielekkäästi tehdä SQL:ssä
- [x] Käytetty try/except SQL-komennon ympärillä vain aiheellisesti

### Sovelluksen turvallisuus (20 p)
- [x] Salasanat tallennetaan tietokantaan asianmukaisesti
- [x] Käyttäjän oikeus nähdä sivun sisältö tarkastetaan
- [x] Käyttäjän oikeus lähettää lomake tarkastetaan
- [x] Käyttäjän syötteet tarkastetaan ennen tietokantaan lisäämistä
- [x] SQL-komennoissa käytetty parametreja
- [x] Sivut muodostetaan sivupohjien kautta
- [x] Lomakkeissa on estetty CSRF-aukko

### Suuren tietomäärän käsittely (5 p)
- [x] Sovellusta testattu suurella tietomäärällä ja raportoitu tulokset
- [x] Sovelluksessa käytössä tietokohteiden sivutus
- [x] Tietokantaan lisätty indeksi, joka nopeuttaa suuren tietomäärän käsittelyä

## Sovelluksen toiminnot

✅ = toteutettu

### Pääkäyttäjä
- Pääkäyttäjä luodaan automaattisesti. ✅
- Pääkäyttäjä voi luoda, muokata ja poistaa käyttäjiä. ✅
- Pääkäyttäjä voi luoda, muokata ja poistaa kilpailutöitä. ✅
- Pääkäyttäjä voi luoda, muokata ja poistaa kilpailuja. ✅
- Pääkäyttäjä voi suodattaa kilpailutöitä kilpailun ja käyttäjän nimen perusteella. ✅
- Pääkäyttäjä voi valita kilpailulle luokittelun: ✅
    - Anonyymi arviointi: kirjoittaja ei ole tunnistettavissa ✅
    - Avoin arviointi: kaikki saavat arvioida kilpailutöitä ✅
    - Tulokset julkisia: kaikki näkevät kilpailun tulokset ✅
	- Kirjallisuuslaji: runo/aforismi/essee ✅

### Käyttäjät
- Käyttäjä voi luoda, muokata ja poistaa tunnuksen. ✅
- Käyttäjä voi kirjautua sisään sovellukseen. ✅
- Käyttäjä näkee sovellukseen lisätyt kilpailut. ✅
- Käyttäjä pystyy etsimään kilpailuja hakusanalla.
- Käyttäjä voi lisätä, muokata ja poistaa oman tekstin. ✅
- Tekstin muokkaus ja poisto on sallittu vain kilpailun keräysvaiheessa. ✅
- Käyttäjä voi arvioida muiden kilpailutöitä antamalla pistemäärän 1-5. ✅
- Sovelluksessa on käyttäjäsivu ("Tekstisi"-sivu) kilpailuista. ✅
- Käyttäjäsivu on käyttäjän sijoitus ja pistemäärä päättyneiden kilpailujen osalta. ✅
- Käyttäjä voi tarkastella kilpailun tuloksia. ✅

## Tietokantarakenne

![Tietokantarakenne](/images/dark_database.png)

## Suuret tietomäärät

Testasin tietokannan nopeutta suurilla tietomäärillä ilman indeksejä ja lisäämällä indeksit. Haut, jotka kohdistuvat suuriin tietomääriin nopeutuivat merkittävästi:

### 10 000 reviews
```
Step 1: Recreate DB and populate with random data...

--- Table Record Counts ---
Users     : 1001
Contests  : 100
Entries   : 5000
Reviews   : 10000
Classes   : 5
Step 2: Timing queries WITHOUT indexes...
Step 3: Adding indexes...
Step 4: Timing queries WITH indexes...

--- Table Record Counts ---
Users     : 1001
Contests  : 100
Entries   : 5000
Reviews   : 10000
Classes   : 5

--- Query Timing Comparison ---
Query                                    | No Index (s) | With Index (s) |  Speedup
--------------------------------------------------------------------------------
search_user_by_username                  |     0.000074 |       0.000088 |     0.84x
list_entries_for_contest                 |     0.000136 |       0.000160 |     0.86x
list_entries_for_user                    |     0.002259 |       0.000022 |   102.10x
search_entries_by_username               |     0.002740 |       0.003433 |     0.80x
list_reviews_for_entry                   |     0.000691 |       0.000047 |    14.76x
list_contests_for_class                  |     0.000058 |       0.000084 |     0.69x
--------------------------------------------------------------------------------
```
### 100 000 reviews
```
--- Table Record Counts ---
Users     : 1001
Contests  : 1000
Entries   : 50000
Reviews   : 100000
Classes   : 5
Step 2: Timing queries WITHOUT indexes...
Step 3: Adding indexes...
Step 4: Timing queries WITH indexes...

--- Table Record Counts ---
Users     : 1001
Contests  : 1000
Entries   : 50000
Reviews   : 100000
Classes   : 5

--- Query Timing Comparison ---
Query                                    | No Index (s) | With Index (s) |  Speedup
--------------------------------------------------------------------------------
search_user_by_username                  |     0.000087 |       0.000082 |     1.06x
list_entries_for_contest                 |     0.000223 |       0.000207 |     1.08x
list_entries_for_user                    |     0.024582 |       0.000233 |   105.69x
search_entries_by_username               |     0.033925 |       0.033920 |     1.00x
list_reviews_for_entry                   |     0.007820 |       0.000063 |   124.88x
list_contests_for_class                  |     0.000487 |       0.000419 |     1.16x
--------------------------------------------------------------------------------
```
### 1 000 000 reviews
```
--- Table Record Counts ---
Users     : 1001
Contests  : 10000
Entries   : 500000
Reviews   : 1000000
Classes   : 5
Step 2: Timing queries WITHOUT indexes...
Step 3: Adding indexes...
Step 4: Timing queries WITH indexes...

--- Table Record Counts ---
Users     : 1001
Contests  : 10000
Entries   : 500000
Reviews   : 1000000
Classes   : 5

--- Query Timing Comparison ---
Query                                    | No Index (s) | With Index (s) |  Speedup
--------------------------------------------------------------------------------
search_user_by_username                  |     0.000082 |       0.000086 |     0.96x
list_entries_for_contest                 |     0.000283 |       0.000204 |     1.39x
list_entries_for_user                    |     0.221362 |       0.001838 |   120.46x
search_entries_by_username               |     0.305147 |       0.311820 |     0.98x
list_reviews_for_entry                   |     0.077450 |       0.000070 |  1109.75x
list_contests_for_class                  |     0.003987 |       0.003726 |     1.07x
--------------------------------------------------------------------------------
```
### 10 000 users, 1 000 000 reviews
```
--- Table Record Counts ---
Users     : 10001
Contests  : 10000
Entries   : 500000
Reviews   : 1000000
Classes   : 5
Step 2: Timing queries WITHOUT indexes...
Step 3: Adding indexes...
Step 4: Timing queries WITH indexes...

--- Table Record Counts ---
Users     : 10001
Contests  : 10000
Entries   : 500000
Reviews   : 1000000
Classes   : 5

--- Query Timing Comparison ---
Query                                    | No Index (s) | With Index (s) |  Speedup
--------------------------------------------------------------------------------
search_user_by_username                  |     0.000077 |       0.000082 |     0.94x
list_entries_for_contest                 |     0.004344 |       0.000214 |    20.26x
list_entries_for_user                    |     2.409421 |       0.000147 | 16399.88x
search_entries_by_username               |     0.407845 |       0.386730 |     1.05x
list_reviews_for_entry                   |     0.070866 |       0.000082 |   863.79x
list_contests_for_class                  |     0.004155 |       0.003808 |     1.09x
--------------------------------------------------------------------------------
```

## Testikattavuus

Testikattavuus on tällä hetkellä 95 %. Testikattavuusraportti luotiin komennolla `pytest --cov --cov-report=html --cov-report=term`:

```
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
app.py                  37      0   100%
db.py                   43      0   100%
routes/__init__.py       0      0   100%
routes/admin.py        327     25    92%
routes/auth.py         110      0   100%
routes/entries.py      191     27    86%
routes/main.py          91      0   100%
sql.py                 169      0   100%
users.py                80      0   100%
utils.py                30      0   100%
--------------------------------------------------
TOTAL                 1078     52    95%
```
