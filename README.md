# Kirjoituskilpailusovellus

Kirjoituskilpailusovelluksen (Writing Contest Web App) avulla voidaan järjestää kirjoituskilpailuja, joissa kerätään ja arvioidaan lyhyitä tekstejä, kuten runoja, aforismeja tai proosaa.

## Sovelluksen toiminnot

### Pääkäyttäjä
- Pääkäyttäjä luodaan automaattisesti.
- Pääkäyttäjä voi luoda, muokata ja poistaa käyttäjiä.
- Pääkäyttäjä voi luoda, muokata ja poistaa tekstejä.
- Pääkäyttäjä voi luoda, muokata ja poistaa kilpailuja.
- Pääkäyttäjä voi valita kilpailulle luokittelun:
	- arviointi: julkinen/piilotettu
	- tulokset: julkinen/piilotettu
	- luokka: runo/aforismi/proosa
	- anonyymi: kyllä/ei.

### Käyttäjät
- Käyttäjä voi luoda, muokata ja poistaa tunnuksen.
- Käyttäjä voi kirjautua sisään sovellukseen.
- Käyttäjä näkee sovellukseen lisätyt kilpailut.
- Käyttäjä pystyy etsimään kilpailuja hakusanalla.
- Käyttäjä voi lisätä, muokata ja poistaa oman tekstin kirjoituskilpailuun.
- Käyttäjä voi arvioida muiden tekstejä antamalla pistemäärän 1-5 ja valinnaisen perustelun.
- Sovelluksessa on käyttäjäsivut, jotka näyttävät listan kilpailuista, joihin käyttäjä on osallistunut.
- Käyttäjä voi tarkastella kilpailun tuloksia.

## Tietokohteet

### Pääkäyttäjä
- käyttäjätunnus
- salasana

### Käyttäjä
- Nimi tai nimimerkki
- Sähköpostiosoite (käyttäjätunnus)
- Salsana

### Kilpailu
- Nimi, kuvaus, säännöt
- Luokka: runo/aforismi/proosa
- Anonyymi: kyllä/ei
- Arviointi: julkinen/piilotettu
- Tulokset: julkinen/piilotettu
- Keräyksen alkamis- ja päättymisaika
- Arvioinnin alkamis- ja päättymisaika

### Kilpailuteksti
- Teksti
- Linkittyy kilpailuun, käyttäjään (kirjoittaja)

### Arvio
- Pistemäärä
- Perustelu
- Linkittyy tekstiin, käyttäjään (arvioija)

## Sovelluksen asennus

Asenna `flask`-kirjasto:

```
$ pip install flask
```

Luo tietokannan taulut ja lisää alkutiedot:

```
$ sqlite3 database.db < schema.sql
$ sqlite3 database.db < init.sql
```

Voit käynnistää sovelluksen näin:

```
$ flask run
```
