# Tasks

## 1. Megcsináltam checkbox (mindkét fájl)

- [x] 1.1 `index_5a.html`: `doneSet` globális változó (`hz_done_5a` localStorage kulcs). `toggleDone(id, e)` függvény: set toggle + localStorage mentés + `renderList()`. CSS: `.card.done { opacity:.5 }` + `.card.done .subj { text-decoration:line-through }`. Ellenőrzés: pipára kattintva a kártya elhalványul és áthúzódik a tantárgy neve.
- [x] 1.2 `index_5a.html`: `cardHTML()`-be pipa gomb hozzáadása a badge elé (jobb oldal). `renderList()` sort kiegészítése: kész elemek a lista végére kerülnek (lejárt elemek után). Ellenőrzés: kész feladat a lista aljára kerül; frissítés után megmarad az állapot.
- [x] 1.3 `index_7a.html`: ugyanazok a változtatások mint 1.1 + 1.2, kulcs: `hz_done_7a`. Ellenőrzés: azonos.

## 2. Due date előtöltés (mindkét fájl)

- [x] 2.1 `index_5a.html`: `openAddSheet(null)` ágban a `document.getElementById('newDue').value=''` sort lecserélni holnap ISO dátumára. Szerkesztés ág (id !== null) változatlan. Ellenőrzés: FAB gomb → „+" form megnyílik holnap dátumával.
- [x] 2.2 `index_7a.html`: ugyanaz. Ellenőrzés: azonos.

## 3. Sürgős sticky sáv (mindkét fájl)

- [x] 3.1 `index_5a.html`: HTML-be `<div id="urgentBanner" style="display:none">` elem a `hwList` div elé. CSS: narancs/piros háttér, padding, border-radius, cursor pointer, `margin-bottom:8px`. `renderUrgentBanner(items)` függvény: az `items` listából szűri a ma/holnap esedékeseket, ha van → banner megjelenik a legközelebbivel, onclick → `document.querySelector('[data-id="'+id+'"]').scrollIntoView({behavior:'smooth',block:'center'})`. `renderList()` végén hívódik. Ellenőrzés: holnapi feladattal a banner megjelenik és tapra a kártyára ugrik.
- [x] 3.2 `index_7a.html`: ugyanaz. Ellenőrzés: azonos.

## 4. Tantárgy szín kódolás (mindkét fájl)

- [x] 4.1 `index_5a.html`: `subjectColor(s)` függvény (hash-alapú HSL szín, `effectiveDue` közelében). `cardHTML()`-ben: ha nincs típus-alapú border-left szín, a kártyán `border-left:4px solid ${subjectColor(h.subject)}` jelenik meg. Ellenőrzés: különböző tantárgyú kártyák különböző szín csíkot kapnak; ugyanaz a tantárgy mindig ugyanolyan színt kap.
- [x] 4.2 `index_7a.html`: ugyanaz. Ellenőrzés: azonos.

## 5. Tab urgencia badge (mindkét fájl)

- [x] 5.1 `index_5a.html`: `renderList()` végén a tab szöveg frissítésekor ellenőrzi, van-e ma esedékes aktív feladat (`effectiveDue` alapján). Ha igen: `'📋 Feladatok (N) 🔴'`. Ellenőrzés: mai due-jú feladattal a tab tartalmazza a 🔴 jelzést; holnapi feladatnál nem jelenik meg.
- [x] 5.2 `index_7a.html`: ugyanaz. Ellenőrzés: azonos.

## 6. Verzió bump

- [x] 6.1 Mindkét fájlban `App v14.9` → `App v15.0` (5 UX funkció = minor verzióugrás).
