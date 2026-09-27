# Proposal

## Why

A feladatlistában az üres határidőjű elemek (pl. órai anyagok) a sorrendben véletlenszerűen jelennek meg, elfedve a valóban sürgős feladatokat (pl. holnapi témazáró). A feltöltés-dátum szerinti alaprendezés nem tükrözi az időbeli sürgősséget.

## What Changes

- **Alapértelmezett határidő**: Ha egy feladat feltöltésekor nincs határidő megadva, automatikusan `feltöltés dátuma + 7 nap` kerül mentésre. Meglévő, határidő nélküli elemek ezt az értéket kapják megjelenítéskor (frontend számítás, nem backfill).
- **Alapértelmezett rendezés**: A feladatlista alapból határidő szerint növekvő sorrendben jelenik meg (a jelenlegi feltöltés-dátum csökkenő helyett). A rendezési preferencia localStorage-ban megmarad.
- **Csoportos nézet gomb**: Új váltógomb a meglévő rendező gombok mellé. Aktív állapotban a lista szekciókba rendeződik: *Ma & Holnap*, *Ezen a héten*, *Később*, *Lejárt*. A preferencia localStorage-ban megmarad.
- Mindkét aktív fájlra alkalmazandó: `index_5a.html` és `index_7a.html`.

## Capabilities

### New Capabilities

- `feladat-rendezés`: A feladatlista rendezési és csoportosítási logikája — alapértelmezett határidő-számítás, rendezési sorrend és a csoportos nézet.

### Modified Capabilities

*(nincs meglévő spec)*

## Impact

- `index_5a.html`, `index_7a.html`: frontend JS és CSS módosítások
- Google Sheets adat: nem változik (az alapértelmezett határidő csak frontend-en számított, nem íródik vissza)
- localStorage kulcsok: `hz_sort_5a` / `hz_sort_7a` (rendezési preferencia), `hz_view_5a` / `hz_view_7a` (lista vs. csoportos nézet)
