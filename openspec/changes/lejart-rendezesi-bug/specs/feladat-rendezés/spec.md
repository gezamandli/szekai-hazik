# Spec Delta

## MODIFIED Requirements

### Requirement: Alapértelmezett rendezés határidő szerint

A feladatlista SHALL alapból határidő szerint növekvő sorrendben jelenjen meg. A felhasználó rendezési preferenciáját a rendszer localStorage-ban kell megőrizze oldalfrissítés között.

Határidő szerinti rendezésnél a lejárt elemek (effectiveDue < mai nap) SHALL mindig a lista végére kerüljenek, függetlenül a növekvő/csökkenő iránytól. Lejárt elemek egymás között dátum szerint rendezve jelennek meg.

#### Scenario: Oldalletöltés

- **WHEN** az alkalmazás betölt és nincs mentett rendezési preferencia
- **THEN** a lista határidő szerint növekvő sorrendben jelenik meg

#### Scenario: Preferencia megőrzése

- **WHEN** felhasználó rendezési módot vált
- **THEN** a preferencia localStorage-ba kerül és következő betöltésnél helyreáll

#### Scenario: Lejárt elemek a lista végén — növekvő rendezés

- **WHEN** határidő szerinti növekvő rendezés aktív és vannak lejárt elemek
- **THEN** a lejárt elemek a lista aljára kerülnek; az aktív/jövőbeli elemek előrébb jelennek meg

#### Scenario: Lejárt elemek a lista végén — csökkenő rendezés

- **WHEN** határidő szerinti csökkenő rendezés aktív és vannak lejárt elemek
- **THEN** a lejárt elemek a lista aljára kerülnek; a legtávolabbi jövőbeli elemek jelennek meg legelőre
