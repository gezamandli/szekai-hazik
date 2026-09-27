# Tasks

## 1. effectiveDue segédfüggvény (mindkét fájl)

- [x] 1.1 `index_5a.html`: Add `effectiveDue(h)` függvényt a `dueInfo()` közelébe — visszaadja `h.due`-t ha van, különben `h.uploaded + 7 nap` (ISO dátum string). Ellenőrzés: `effectiveDue({due:'2026-10-01', uploaded:'2026-09-27'})` === `'2026-10-01'`, `effectiveDue({due:'', uploaded:'2026-09-20T10:00:00Z'})` === `'2026-09-27'`.
- [x] 1.2 `index_7a.html`: Ugyanaz az `effectiveDue(h)` függvény beillesztése. Ellenőrzés: ugyanazok a tesztek mint 1.1-nél.

## 2. dueInfo és cardHTML frissítése (mindkét fájl)

- [x] 2.1 `index_5a.html`: `dueInfo(h.due)` hívásokat `dueInfo(effectiveDue(h))` formára cserélni a `cardHTML()`, `renderNotifyList()` és egyéb megjelenítő helyeken. A `dueInfo()` belső `if(!ds||ds==='')` ágát eltávolítani (már nem hívódik üres stringgel). Ellenőrzés: üres due-jú kártyán nem jelenik meg "Nincs határidő" badge, helyette a +7 napos badge látszik.
- [x] 2.2 `index_7a.html`: Ugyanazok a változtatások mint 2.1. Ellenőrzés: azonos.

## 3. Új feladat mentésekor due kitöltése (mindkét fájl)

- [x] 3.1 `index_5a.html`: A mentési logikában (ahol `due` változó épül fel a form inputból) — ha `due` üres, `due = effectiveDue({uploaded: new Date().toISOString()})`. Ellenőrzés: due mező üresen hagyva és feladat mentve → a Sheetsben a feltöltés napja + 7 nap jelenik meg.
- [x] 3.2 `index_7a.html`: Ugyanaz mint 3.1. Ellenőrzés: azonos.

## 4. Alapértelmezett rendezés és localStorage megőrzés (mindkét fájl)

- [x] 4.1 `index_5a.html`: `sortBy` alapértéke `'due'`, `sortAsc` alapértéke `true`. Betöltésnél `localStorage.getItem('hz_sort_by_5a')` / `hz_sort_asc_5a` olvassa vissza az értéket, ha létezik. `setSortBy()` híváskor menti. A `renderList()` sort logikában `new Date('9999-12-31')` helyett `new Date(effectiveDue(a))` használatos. Ellenőrzés: oldalfrissítés után a határidő gomb aktív marad; témazáró a lista tetején.
- [x] 4.2 `index_7a.html`: Ugyanaz, kulcsok: `hz_sort_by_7a` / `hz_sort_asc_7a`. Ellenőrzés: azonos.

## 5. Csoportos nézet gomb és renderelés (mindkét fájl)

- [x] 5.1 `index_5a.html`: `groupedView` boolean globális változó (alap: `false`), localStorage kulcs `hz_view_5a`. Betöltésnél visszatölt. CSS: `.group-header` stílus (félkövér szöveg, halvány vonal alatta, kis padding). Gomb HTML a sort gombok mellé: `⚡ Csoportos` toggle, aktív állapot kék háttér (a többi sort gomb stílusával konzisztens). Ellenőrzés: gombra kattintva a lista szekciókba rendezve látszik, újra kattintva visszaáll.
- [x] 5.2 `index_5a.html`: `renderGrouped()` függvény: szekciók Ma & Holnap (diff 0-1), Ezen a héten (diff 2-7), Később (diff 8+), Lejárt (diff < 0). Üres szekciók nem jelennek meg. `renderList()` meghívja `renderGrouped()`-et ha `groupedView===true`. Lejárt kártyák `.65` opacitása megmarad. Ellenőrzés: legalább egy holnapi feladattal a "Ma & Holnap" szekció jelenik meg legelöl.
- [x] 5.3 `index_7a.html`: Ugyanazok a változtatások mint 5.1 + 5.2, kulcs: `hz_view_7a`. Ellenőrzés: azonos.

## 6. Integrációs ellenőrzés

- [x] 6.1 Mindkét fájlban: feladat szűrők (tantárgy chip, típus szűrő, keresés) csoportos nézetben is helyesen működnek — csak a szűrt elemek jelennek meg szekciókban. Ellenőrzés: tantárgy chip kiválasztva → csak az adott tantárgy kártyái látszanak csoportosítva.
- [x] 6.2 Mindkét fájlban: `activeHW()` / értesítési lista (`renderNotifyList`) is `effectiveDue(h)`-t használ rendezéshez. Ellenőrzés: értesítési listában az üres due-jú elemek is rendezve jelennek meg.
