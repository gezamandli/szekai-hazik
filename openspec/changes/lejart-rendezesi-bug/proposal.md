# Proposal

## Why

Határidő szerinti növekvő rendezésnél a lejárt feladatok (múltbeli due date) a lista elejére kerülnek, mert dátumértékük kisebb az aktuális és jövőbeli elemekénél. Ez elfedi a sürgős, ma vagy holnap esedékes feladatokat.

## What Changes

- A határidő szerinti rendezés kiegészül egy szabállyal: lejárt elemek (effectiveDue < mai nap) mindig a lista aljára kerülnek, függetlenül a növekvő/csökkenő iránytól.
- A lejárt elemek egymás között dátum szerint rendezve maradnak.
- Mindkét fájlra alkalmazandó: `index_5a.html` és `index_7a.html`.

## Capabilities

### New Capabilities

*(nincs)*

### Modified Capabilities

- `feladat-rendezés`: A határidő szerinti rendezési szabály kiegészítése — lejárt elemek mindig a lista végén.

## Impact

- `index_5a.html`, `index_7a.html`: a `renderList()` sort logikájának módosítása (~3 sor mindkét fájlban)
- Adatok és localStorage: nem változnak
