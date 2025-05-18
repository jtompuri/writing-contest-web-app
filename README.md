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

### Käyttäjät
- Tunniste
- Nimi tai nimimerkki: teksi
- Käyttäjätunnus (sähköpostiosoite): teksti
- Salasana: teksti
- Pääkäyttäjä: kyllä/ei
- Luontiaika
  
### Kilpailut
- Tunniste
- Nimi: teksti
- Lyhyt kuvaus: teksti 
- Säännöt: teksti
- Luokka: runo/aforismi/proosa
- Anonyymi: kyllä/ei
- Arviointi: julkinen/piilotettu
- Tulokset: julkinen/piilotettu
- Keräyksen päättymisaika
- Arvioinnin päättymisaika
- Luontiaika
 
### Kilpailutyöt
- Tunniste
- Teksti
- Linkittyy kilpailuun, käyttäjään (kirjoittaja)
- Luontiaika
 
### Arvio
- Tunniste
- Pistemäärä: kokonaisluku
- Palaute: teksti
- Linkittyy tekstiin, käyttäjään (arvioija)
- Luontiaika
   
## Työn eteneminen

Työn etenemistä voi seurata alla olevasta tehtävälistasta.

### Välipalautus 1
- [x] Luo GitHubiin julkinen repositorio harjoitustyötä varten. Nimeä repositoriosi kuvaavasti.
- [x] Valitse projektille aihe ja kirjoita README.md-tiedostoon kuvaus, joka esittelee sovelluksen keskeiset toiminnot. 
- [x] Kirjoita kuvaus samassa muodossa kuin aloitussivun esimerkkiaiheissa ja esimerkkisovelluksessa.
- [x] Kirjaudu Labtooliin ja ilmoita siellä projektisi GitHub-osoite.

### Välipalautus 2

- [ ] Tavoitteena on, että sovelluksessa on ainakin seuraavat toiminnot:
	- [ ] Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
	- [ ] Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan tietokohteita.
	- [ ] Käyttäjä näkee sovellukseen lisätyt tietokohteet.
	- [ ] Käyttäjä pystyy etsimään tietokohteita hakusanalla tai muulla perusteella.
- [ ] README.md-tiedoston tulee kuvata, mikä on sovelluksen nykyinen tilanne.

### Välipalautus 3

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
