# Kirjoituskilpailusovellus

Kirjoituskilpailusovelluksen (Writing Contest Web App) avulla voidaan järjestää kirjoituskilpailuja, joissa kerätään ja arvioidaan lyhyitä tekstejä, kuten runoja, aforismeja tai esseitä.

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

Kirjaudu demoon käyttäjätunnuksella `admin` ja salasanalla `admin`.

## Sovelluksen toiminnot (✅ = toteutettu)

### Pääkäyttäjä
- Pääkäyttäjä luodaan automaattisesti. ✅
- Pääkäyttäjä voi luoda, muokata ja poistaa käyttäjiä. ✅
- Pääkäyttäjä voi luoda, muokata ja poistaa tekstejä. ✅
- Pääkäyttäjä voi luoda, muokata ja poistaa kilpailuja. ✅
- Pääkäyttäjä voi valita kilpailulle luokittelun: ✅
	- arviointi: julkinen/piilotettu ✅
	- tulokset: julkinen/piilotettu ✅
	- luokka: runo/aforismi/essee ✅
	- anonyymi: kyllä/ei. ✅

### Käyttäjät
- Käyttäjä voi luoda ✅, muokata ja poistaa tunnuksen.
- Käyttäjä voi kirjautua sisään sovellukseen. ✅
- Käyttäjä näkee sovellukseen lisätyt kilpailut. ✅
- Käyttäjä pystyy etsimään kilpailuja hakusanalla.
- Käyttäjä voi lisätä, muokata ja poistaa oman tekstin kirjoituskilpailuun.
- Käyttäjä voi arvioida muiden tekstejä antamalla pistemäärän 1-5 ja valinnaisen perustelun.
- Sovelluksessa on käyttäjäsivut, jotka näyttävät listan kilpailuista, joihin käyttäjä on osallistunut.
- Käyttäjä voi tarkastella kilpailun tuloksia.

## Tietokohteet

### Käyttäjät
- ID
- Nimi tai nimimerkki: teksi
- Käyttäjätunnus (sähköpostiosoite): teksti
- Salasana: teksti
- Pääkäyttäjä: kyllä/ei
- Luontiaika
  
### Kilpailut
- ID
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
- ID
- Teksti
- Linkittyy kilpailuun, käyttäjään (kirjoittaja)
- Luontiaika
 
### Arvio
- ID
- Pistemäärä: kokonaisluku
- Palaute: teksti
- Linkittyy tekstiin, käyttäjään (arvioija)
- Luontiaika
   
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

- [ ] Tavoitteena on, että sovelluksessa on ainakin seuraavat toiminnot:
	- [ ] Sovelluksessa on käyttäjäsivut, jotka näyttävät tilastoja ja käyttäjän lisäämät tietokohteet.
	- [ ] Käyttäjä pystyy valitsemaan tietokohteelle yhden tai useamman luokittelun. Mahdolliset luokat ovat tietokannassa.
	- [ ] Käyttäjä pystyy lähettämään toisen käyttäjän tietokohteeseen liittyen jotain lisätietoa, joka tulee näkyviin sovelluksessa.
- [ ] README.md-tiedoston tulee kuvata, mikä on sovelluksen nykyinen tilanne.
