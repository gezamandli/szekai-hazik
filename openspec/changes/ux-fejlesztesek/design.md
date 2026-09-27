# Design

## Context

Mindkét fájl (`index_5a.html`, `index_7a.html`) egyetlen HTML fájl beágyazott JS/CSS-sel. A `cardHTML()` generálja a kártyák HTML-jét, `renderList()` kezeli a rendezést és a lista megjelenítését, `openAddSheet()` nyitja a form sheetet.

## Goals / Non-Goals

**Goals:**
- 5 UX finomítás implementálása mindkét fájlban
- Minden localStorage kulcs fájlonként elkülönített (`_5a` / `_7a` suffix)

**Non-Goals:**
- Szerver oldali változtatások
- Más felhasználók állapotának módosítása
- Csoportos nézet érintése

## Decisions

### 1. Megcsináltam — `doneSet` + `renderList` integráció

```js
let doneSet = new Set(JSON.parse(localStorage.getItem('hz_done_7a') || '[]'));

function toggleDone(id, e) {
  e.stopPropagation();
  if (doneSet.has(id)) doneSet.delete(id); else doneSet.add(id);
  localStorage.setItem('hz_done_7a', JSON.stringify([...doneSet]));
  renderList();
}
```

`cardHTML()` kiegészítés: pipa ikon gomb a `card-head` jobb szélén a badge előtt.  
`renderList()` sort kiegészítés: kész elemek a lista végére kerülnek (a lejárt elemek után, vagy előttük — az aktív lejártak is sürgősebbek mint a kész feladatok).

Kész kártya vizuális stílus: `opacity: .5`, `text-decoration: line-through` a subject szövegen.

### 2. Due date előtöltés — `openAddSheet(null)` ágban

```js
// Új feladat esetén (id === null)
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
document.getElementById('newDue').value = tomorrow.toISOString().slice(0, 10);
```

### 3. Sürgős sticky sáv — `renderUrgentBanner()`

Új `<div id="urgentBanner">` elem a `hwList` előtt (HTML-ben). `renderList()` végén hívódik. Ha `activeHW()` között van ma/holnap esedékes, a banner megjelenik és az első ilyen feladatra mutat (`data-target-id` attribútum + scroll onclick). CSS: kék/narancs háttér, position sticky lehetséges de egyszerűen a lista tetején fix.

### 4. Tantárgy szín — `subjectColor(subject)`

```js
function subjectColor(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) & 0xffff;
  return `hsl(${h % 360}, 65%, 45%)`;
}
```

`cardHTML()`-ben a meglévő típus-alapú `border-left` mellé:  
- Ha van típus szín: megtartjuk a típus szín csíkot (témazáró, dolgozat)  
- Ha nincs típus szín: tantárgy szín csík

Így a típus szín prioritást élvez, de típus nélküli feladatoknál is van vizuális kiemelés.

### 5. Tab urgencia badge — `renderList()` végén

```js
const hasToday = activeHW().some(h => {
  const d = new Date(effectiveDue(h)); d.setHours(0,0,0,0);
  return Math.round((d - today0()) / 864e5) === 0;
});
const tabEl = document.getElementById('tab-list');
tabEl.textContent = '📋 Feladatok' + (items.length ? ' (' + items.length + ')' : '') + (hasToday ? ' 🔴' : '');
```

## Risks / Trade-offs

- **Tantárgy szín ütközés típus színnel**: ha valakinek típus és tantárgy egyszerre van, a típus szín kerül előre (prioritás-alapú). Ez szándékos.
- **doneSet és szinkronizálás**: más eszközön / más felhasználónál a kész jelölés nem jelenik meg — ez a design. Dokumentálni kell a súgóban.
- **Banner és szűrő**: ha tantárgy chip aktív és a szűrt listában nincs sürgős elem, a banner eltűnhet, holott van sürgős (de más tantárgyú) feladat. Elfogadott kompromisszum — a banner a látható lista alapján működik.
