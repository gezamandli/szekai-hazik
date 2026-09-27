# Design

## Context

Lásd proposal.md. A `renderList()` sort blokkja mindkét fájlban (~5 sor) az egyetlen érintett hely.

## Goals / Non-Goals

**Goals:**
- Lejárt elemek mindig a lista aljára kerülnek határidő rendezésnél (mindkét irányban)

**Non-Goals:**
- Csoportos nézet érintése (ott a Lejárt szekció már helyesen jelenik meg a végén)
- Feltöltés szerinti rendezés érintése

## Decisions

### Sort key kiegészítés

A jelenlegi sort:
```js
const da = new Date(effectiveDue(a));
const db = new Date(effectiveDue(b));
return sortAsc ? da-db : db-da;
```

Probléma: ascending rendezésnél múltbeli dátumok (kisebb szám) kerülnek előre.

Javítás — lejárt elemeket egy tiebreaker réteggel a végére toljuk:
```js
const t0 = today0();
const da = new Date(effectiveDue(a));
const db = new Date(effectiveDue(b));
const pastA = da < t0, pastB = db < t0;
if (pastA !== pastB) return pastA ? 1 : -1;  // lejárt mindig hátrébb
return sortAsc ? da-db : db-da;
```

Ez mindkét sort irányban működik: a `pastA ? 1 : -1` nem függ `sortAsc`-tól, így lejárt elemek csökkenő rendezésnél is a végén maradnak.

## Risks / Trade-offs

- Minimális: egyetlen feltétel hozzáadása, meglévő logika érintetlen marad.
