# Spec Delta

## Purpose

Vizuális és interakciós finomítások a feladatlista átláthatóságához és a gyors feladat-hozzáadáshoz.

## ADDED Requirements

### Requirement: Due date előtöltés új feladatnál

Amikor a felhasználó új feladat hozzáadására nyitja a formot (nem szerkesztésre), a határidő mező SHALL automatikusan a holnap dátumával legyen előtöltve. Szerkesztésnél a meglévő dátum jelenik meg.

#### Scenario: Új feladat form megnyitása

- **WHEN** a felhasználó az „＋" gombra kattint új feladat hozzáadásához
- **THEN** a határidő mező holnap dátumát mutatja alapértelmezetten

#### Scenario: Szerkesztés form megnyitása

- **WHEN** a felhasználó egy meglévő feladatot szerkeszt
- **THEN** a határidő mező a feladat eredeti due értékét mutatja (változatlan)

---

### Requirement: Sürgős sticky sáv

Ha van ma vagy holnap esedékes aktív feladat, a feladatlista tetején SHALL egy érintható figyelmeztető sáv jelenjen meg a legközelebbi ilyen feladattal. Ha nincs sürgős feladat, a sáv nem jelenik meg.

#### Scenario: Sürgős feladat van

- **WHEN** legalább egy aktív feladat due date-je ma vagy holnap
- **THEN** a lista felett megjelenik a sáv a legközelebbi feladat tantárgyával és badge-ével

#### Scenario: Nincs sürgős feladat

- **WHEN** egyetlen aktív feladatnak sincs ma vagy holnapi due date-je
- **THEN** a sáv nem jelenik meg, a lista normálisan indul

#### Scenario: Sávra kattintás

- **WHEN** a felhasználó a sávra kattint/tipeg
- **THEN** az oldal az adott feladat kártyájához görget

---

### Requirement: Tantárgy szín kódolás

Minden tantárgyhoz a rendszer SHALL konzisztens, az adott osztályban egyedi színt rendelni a tantárgy neve alapján (hash-alapú számítás). A szín a kártyán bal oldali szín csíkként jelenik meg.

#### Scenario: Kártyán megjelenő szín

- **WHEN** egy feladatkártya renderelődik
- **THEN** a kártya bal szélén megjelenik a tantárgyhoz rendelt szín csík

#### Scenario: Konzisztencia

- **WHEN** ugyanaz a tantárgy különböző kártyákon jelenik meg
- **THEN** mindkét kártyán ugyanolyan szín látszik

---

### Requirement: Tab urgencia badge

Ha van ma esedékes aktív feladat, a Feladatok tab felirata SHALL `🔴` jelzést tartalmazzon. Ha nincs, a jelzés nem jelenik meg.

#### Scenario: Van ma esedékes feladat

- **WHEN** legalább egy aktív feladatnak ma a due date-je
- **THEN** a Feladatok tab felirata tartalmazza a `🔴` jelzést

#### Scenario: Nincs ma esedékes feladat

- **WHEN** egyetlen aktív feladatnak sincs mai due date-je
- **THEN** a tab felirata a szokásos formában jelenik meg, jelzés nélkül
