# Spec Delta

## Purpose

A feladatlista rendezési és csoportosítási logikáját határozza meg: alapértelmezett határidő-számítás üres due esetén, alapértelmezett rendezési sorrend és opcionális csoportos nézetváltás.

## ADDED Requirements

### Requirement: Alapértelmezett határidő számítás

Ha egy feladat `due` mezője üres vagy hiányzik, a rendszer SHALL az elemet úgy kezelje, mintha a határideje `feltöltés dátuma + 7 nap` lenne — rendezéshez, csoportosításhoz és a dueInfo badge megjelenítéséhez. Ez az érték NEM kerül visszaírásra a Google Sheetsbe.

#### Scenario: Üres due megjelenítése

- **WHEN** egy feladat `due` mezője üres
- **THEN** a rendszer `feltöltés + 7 nap` értékkel számol a badge és a rendezés szempontjából

#### Scenario: Új feladat mentése due nélkül

- **WHEN** felhasználó új feladatot ment el üresen hagyott határidővel
- **THEN** a mentett `due` értéke `feltöltés dátuma + 7 nap` (ISO dátum string)

---

### Requirement: Alapértelmezett rendezés határidő szerint

A feladatlista SHALL alapból határidő szerint növekvő sorrendben jelenjen meg. A felhasználó rendezési preferenciáját a rendszer localStorage-ban kell megőrizze oldalfrissítés között.

#### Scenario: Oldalletöltés

- **WHEN** az alkalmazás betölt és nincs mentett rendezési preferencia
- **THEN** a lista határidő szerint növekvő sorrendben jelenik meg

#### Scenario: Preferencia megőrzése

- **WHEN** felhasználó rendezési módot vált
- **THEN** a preferencia localStorage-ba kerül és következő betöltésnél helyreáll

---

### Requirement: Csoportos nézet váltógomb

A feladatlistán SHALL megjelenjen egy csoportos nézet váltógomb a meglévő rendező gombok mellett. Aktív állapotban a lista az alábbi szekciókba rendeződik:

- **Ma & Holnap** — due date ma vagy holnap
- **Ezen a héten** — due date 2–7 napon belül
- **Később** — due date 8+ nap
- **Lejárt** — due date a mai napnál korábbi

Üres szekciók nem jelennek meg. A nézet-preferencia localStorage-ban megmarad.

#### Scenario: Csoportos nézet bekapcsolása

- **WHEN** felhasználó a csoportos nézet gombra kattint
- **THEN** a feladatok szekciókba rendezve jelennek meg, üres szekciók nélkül

#### Scenario: Sürgős szekció prioritás

- **WHEN** csoportos nézet aktív és van ma vagy holnap esedékes feladat
- **THEN** a "Ma & Holnap" szekció a lista tetején jelenik meg

#### Scenario: Visszaváltás lista nézetre

- **WHEN** felhasználó ismét a csoportos nézet gombra kattint
- **THEN** a feladatok visszatérnek a hagyományos rendezett lista nézetbe
