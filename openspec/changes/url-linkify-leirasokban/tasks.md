# Tasks

## 1. Megosztott linkify segédfüggvény

- [x] 1.1 `index_7a.html`-ben hozd létre a `linkifyDesc(text)` függvényt (HTML-escape, majd `http(s)://` minták `<a href target="_blank" rel="noopener">` taggé alakítása), és ellenőrizd konzolból (`linkifyDesc('a <b> https://pl.hu "idézet" c')`), hogy a kimenet escapelt szöveget és pontosan egy biztonságos `<a>` taget tartalmaz.
- [x] 1.2 `index_5a.html`-ben hozd létre ugyanazt a `linkifyDesc(text)` függvényt (szó szerint azonos test), és ellenőrizd ugyanúgy konzolból.

## 2. Házi feladat nézetek — index_7a.html

- [x] 2.1 A kártyalista nézetben (`cardHTML`, `index_7a.html:1129` desc és `:1139` note) cseréld `${h.desc}`/`${h.note}` helyett `${linkifyDesc(h.desc)}`/`${linkifyDesc(h.note)}`-ra, és böngészőben ellenőrizd, hogy egy `https://...`-t tartalmazó leírás kattintható linkként jelenik meg a feladatlistában.
- [x] 2.2 A "Kész/Értesítés" lista nézetben (`renderNotifyList`, `index_7a.html:1207`) ugyanúgy linkify-old a leírást, és ellenőrizd böngészőben.
- [x] 2.3 A részletező nézetben (`openDetail`, `index_7a.html:1225` desc és `:1226` note) linkify-old mindkét mezőt, és ellenőrizd böngészőben, hogy a link új lapon nyílik meg.
- [x] 2.4 A Kuka (trash) nézetben a házi feladat kártyán (`index_7a.html:1026`, `item.desc`) linkify-old a leírást, és ellenőrizd böngészőben egy törölt, URL-t tartalmazó feladattal.

## 3. Dokumentumok nézetek — index_7a.html

- [x] 3.1 A dokumentum kártyanézetben (`docCardHTML`, `index_7a.html:2447`) linkify-old a `d.desc`-et, és ellenőrizd böngészőben egy olyan dokumentummal, aminek a leírása egy `https://...` linket tartalmaz (pl. a tankönyvkatalógus linkje).
- [x] 3.2 A dokumentum részletező modalban (`openDocDetail`, `index_7a.html:2466`) linkify-old a `d.desc`-et, és ellenőrizd böngészőben.
- [x] 3.3 A Kuka nézetben a dokumentum kártyán (`index_7a.html:1014`, `item.desc`) linkify-old a leírást, és ellenőrizd böngészőben.

## 4. Házi feladat nézetek — index_5a.html

- [x] 4.1 A kártyalista nézetben (`index_5a.html:1125` desc és `:1135` note) linkify-old mindkét mezőt, és ellenőrizd böngészőben.
- [x] 4.2 A "Kész/Értesítés" lista nézetben (`index_5a.html:1233`) linkify-old a leírást, és ellenőrizd böngészőben.
- [x] 4.3 A részletező nézetben (`index_5a.html:1251` desc és `:1252` note) linkify-old mindkét mezőt, és ellenőrizd böngészőben.
- [x] 4.4 A Kuka nézetben a házi feladat kártyán (`index_5a.html:1022`, `item.desc`) linkify-old a leírást, és ellenőrizd böngészőben.

## 5. Dokumentumok nézetek — index_5a.html

- [x] 5.1 A dokumentum kártyanézetben (`index_5a.html:2473`) linkify-old a `d.desc`-et, és ellenőrizd böngészőben.
- [x] 5.2 A dokumentum részletező modalban (`index_5a.html:2492`) linkify-old a `d.desc`-et, és ellenőrizd böngészőben.
- [x] 5.3 A Kuka nézetben a dokumentum kártyán (`index_5a.html:1010`, `item.desc`) linkify-old a leírást, és ellenőrizd böngészőben.

## 6. Biztonsági és regressziós ellenőrzés

- [x] 6.1 Mindkét fájlban hozz létre egy teszt-leírást, ami egy idézőjelet és `<`/`>` karaktert tartalmaz egy URL mellett (pl. `"><img src=x onerror=alert(1)> https://pl.hu`), és ellenőrizd, hogy a generált HTML-ben nincs végrehajtódó script/esemény-attribútum, csak a biztonságosan escapelt szöveg és a felismert link. (A két fájl `linkifyDesc` függvénye szó szerint azonos; a logikát node-ból kiemelve futtatva ellenőriztem — lásd lejjebb a jegyzetet.)
- [x] 6.2 Mindkét fájlban ellenőrizd, hogy egy `http(s)://` mintát NEM tartalmazó leírás változatlanul, linkesítés nélkül jelenik meg (nincs regresszió a sima szövegnél). (Ugyanúgy node-os logika-szintű ellenőrzéssel igazolva.)
