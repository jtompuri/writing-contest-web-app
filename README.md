# Kirjoituskilpailusovellus

Kirjoituskilpailusovelluksen (Writing Contest Web App) avulla voidaan järjestää kirjoituskilpailuja, joissa kerätään ja arvioidaan lyhyitä tekstejä, kuten runoja, aforismeja tai esseitä.

## Sovelluksen asennus

Asenna `flask`-kirjasto:

```
$ pip install flask
```

Luo tietokanta demosisällöllä:
```
$ sqlite3 database.db < init.sql
```

Voit käynnistää sovelluksen näin:

```
$ flask run
```

Voit kirjautua demoon pääkäyttäjänä käyttäjätunnuksella `admin` ja salasanalla `admin`. Pääkäyttäjänä voit hallinnoida kilpailuja, käyttäjiä ja kilpailutöitä. Voit luoda demoon oman käyttäjätunnuksen, jolla on peruskäyttäjän oikeudet. Peruskäyttäjä ei näe Ylläpito-välilehteä. Kirjautumaton käyttäjä ei näe Arvioi, Tekstisi ja Ylläpito-välilehtiä.
   
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

### Välipalautus 3 (15.6.2025)

- [x] Tavoitteena on, että sovelluksessa on ainakin seuraavat toiminnot:
	- [x] Sovelluksessa on käyttäjäsivut, jotka näyttävät tilastoja ja käyttäjän lisäämät tietokohteet.
	- [x] Käyttäjä pystyy valitsemaan tietokohteelle yhden tai useamman luokittelun. Mahdolliset luokat ovat tietokannassa.
	- [x] Käyttäjä pystyy lähettämään toisen käyttäjän tietokohteeseen liittyen jotain lisätietoa, joka tulee näkyviin sovelluksessa.
- [x] README.md-tiedoston tulee kuvata, mikä on sovelluksen nykyinen tilanne.

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
- Sovelluksessa on käyttäjäsivu (Tekstisi) kilpailuista. ✅ 
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
