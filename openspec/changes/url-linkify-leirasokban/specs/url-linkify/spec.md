# Spec Delta

## Purpose

Szabadszöveges leírás-mezőkben megjelenő webcímek automatikus, biztonságos kattinthatóvá alakítása, hogy a felhasználók állandó referenciaként elhelyezett linkjei ténylegesen linkként működjenek.

## ADDED Requirements

### Requirement: URL-ek linkesítése a házi feladat leírásában
A rendszer a házi feladat leírás (`desc`) és megjegyzés (`note`) mezőjének megjelenítésekor a szövegben található `http://` vagy `https://` kezdetű URL-eket kattintható, új lapon megnyíló linkké SHALL alakítsa.

#### Scenario: URL-t tartalmazó leírás megjelenítése
- **WHEN** egy házi feladat leírása tartalmaz egy `https://...` kezdetű szövegrészt
- **THEN** a feladat kártya- vagy részletnézetében az adott szövegrész kattintható linkként jelenik meg, ami új lapon nyitja meg a célt

#### Scenario: Leírás URL nélkül
- **WHEN** egy házi feladat leírása nem tartalmaz `http://` vagy `https://` mintát
- **THEN** a leírás változatlanul, linkesítés nélkül jelenik meg

### Requirement: URL-ek linkesítése a dokumentum leírásában
A rendszer a Dokumentumok tab egy dokumentumának leírás (`desc`) mezőjét megjelenítésekor a szövegben található `http://` vagy `https://` kezdetű URL-eket kattintható, új lapon megnyíló linkké SHALL alakítsa, mind a dokumentum kártyanézetében, mind a részletező nézetében.

#### Scenario: Referencia link egy dokumentum leírásában
- **WHEN** a felhasználó felvesz egy dokumentumot, és a leírásába bemásol egy külső webcímet (pl. egy tankönyvkatalógus linket)
- **THEN** a dokumentum kártyáján és a részletező nézetében a webcím kattintható linkként jelenik meg

### Requirement: Biztonságos linkesítés
A linkesítés SHALL ne tegye lehetővé tetszőleges HTML vagy HTML-attribútum beszúrását a felismert URL értékén keresztül; a generált link `href` attribútuma kizárólag a felismert URL-t SHALL tartalmazza, idézőjel vagy HTML-jelölés karakterek nélkül.

#### Scenario: Idézőjelet tartalmazó szöveg a link mellett
- **WHEN** a leírás egy URL-t közvetlenül `"` vagy `<`/`>` karakterrel körülvéve tartalmaz
- **THEN** a generált `<a>` elem `href` attribútuma nem tartalmaz a felismert URL-en kívüli, a leírásból származó HTML-jelölést vagy attribútum-határoló karaktert
