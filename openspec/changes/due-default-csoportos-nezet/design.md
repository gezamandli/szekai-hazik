# Design

## Context

Mindkét aktív fájl (`index_5a.html`, `index_7a.html`) egyetlen HTML fájl, beágyazott JS-sel és CSS-sel, nincs build rendszer. A backend Google Apps Script + Google Sheets; a frontend localStorage-t használ session, homework cache és favorites tároláshoz. A rendezési logika a `renderList()` függvényben él, a `sortBy` / `sortAsc` globális változókkal vezérelve. A `dueInfo()` függvény kezeli a badge megjelenítést.

## Goals / Non-Goals

**Goals:**
- `effectiveDue(h)` segédfüggvény: `h.due || (uploaded + 7 nap)` — egy helyen, mindenhol referenciaként
- Alapértelmezett sort `due` ascending az első betöltésnél
- Sort preferencia localStorage-ba mentve / visszatöltve
- Csoportos nézet gomb; állapota localStorage-ban megmarad
- Párhuzamos alkalmazás: `index_5a.html` és `index_7a.html` (különálló localStorage kulcsokkal)

**Non-Goals:**
- Google Sheets backfill — a `due` mező nem módosul a Sheetsben
- Dark mode, PWA, swipe gesztusok

## Decisions

### 1. `effectiveDue(h)` segédfüggvény — ne ismétlődjön a logika

Minden helyen, ahol jelenleg `h.due` szerepel rendezéshez vagy megjelenítéshez, `effectiveDue(h)` hívás váltja fel.

```js
function effectiveDue(h) {
  if (h.due) return h.due;
  const d = new Date(h.uploaded);
  d.setDate(d.getDate() + 7);
  return d.toISOString().slice(0, 10);
}
```

Alternatíva volt az inline `h.due || fallback` mindenhol — elutasítva, mert ~8 helyen kellene ismételni és inkonzisztencia kockázatát hordozza.

### 2. Új feladat mentésekor `effectiveDue` kerül a `due` mezőbe

Ha a form `due` inputja üres marad, a mentési logikában `due = effectiveDue({uploaded: new Date().toISOString()})` számítódik. Így a Sheetsbe is konkrét dátum kerül, nem üres string — az Apps Script oldala nem változik.

### 3. Sort preferencia localStorage kulcsok

- `index_5a.html`: `hz_sort_by_5a`, `hz_sort_asc_5a`
- `index_7a.html`: `hz_sort_by_7a`, `hz_sort_asc_7a`

Az `init()` / `loadSheet()` során töltődnek be; az alapértelmezett `due` / `true` (ascending) akkor lép életbe, ha nincs mentett érték.

### 4. Csoportos nézet: CSS class váltás, nem külön DOM struktúra

A `hwList` konténerbe szekció-elválasztók (`<div class="group-header">`) kerülnek a kártyák közé, nem egy teljesen új lista épül fel. Ez minimalizálja a kód duplikációt — a `cardHTML()` változatlan marad.

```
groupedView=true  →  renderList() szekció headerekkel
groupedView=false →  renderList() lapos lista (jelenlegi)
```

Nézet preferencia kulcsok: `hz_view_5a` / `hz_view_7a`.

### 5. Lejárt feladatok szekciója csoportos nézetben

Csoportos nézetben a lejárt feladatok a lista végén, "Lejárt" szekció alatt jelennek meg — a jelenlegi `.65` opacitás megmarad. Szekció akkor jelenik meg, ha legalább egy lejárt elem van.

## Risks / Trade-offs

- **Két fájl szinkronja**: A változtatások `index_5a.html`-ben és `index_7a.html`-ben párhuzamosan hajtandók végre — eltérés esetén a két verzió inkonzisztens marad. Kockázat: copy-paste hiba. Csökkentés: a tasks.md mindkét fájlban explicit feladatokat sorol.
- **Meglévő üres due mezők**: Frontend `effectiveDue()` kezeli ezeket, de a Sheetsben üres marad. Ha valaki közvetlenül Sheetsből néz adatot, nem látja a +7 napos értéket. Elfogadott kompromisszum: a backfill felesleges plexitás lenne.
- **dueInfo() és effectiveDue() összhangja**: A `dueInfo()` jelenleg `if(!ds||ds==='')` ágon adja vissza a "Nincs határidő" badge-et. Az `effectiveDue()`-val hívva ez az ág soha nem aktiválódik — a "Nincs határidő" badge eltűnik. Ez szándékos, de tudatosnak kell lenni.
