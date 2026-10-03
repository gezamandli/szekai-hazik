# Proposal

## Why

Sem a házi feladatok, sem a Dokumentumok tab leírás-mezőiben nincs semmilyen linkesítési logika: ha a felhasználó egy `http(s)://` URL-t ír be szabad szövegként (pl. egy állandó referenciaként használt tankönyvkatalógus-linket), az a megjelenítésben sima, nem kattintható szöveg marad. A felhasználó szeretne egy osztályonként eltérő tankönyvkatalógus-linket eltárolni referenciaként egy dokumentum leírásában, ezért a leírásokban megjelenő URL-eknek kattintható linkként kell működniük.

## What Changes

- A házi feladat leírás/megjegyzés mezőinek (`h.desc`, `h.note`) és a Dokumentumok leírás mezőjének (`d.desc`) megjelenítésekor egy linkify logika felismeri a szövegben lévő `http(s)://...` mintákat, és `<a href="..." target="_blank" rel="noopener">` linkké alakítja őket.
- A linkify ugyanazon a logikán (azonos segédfüggvényen) megy végig mindenhol, ahol ezek a mezők megjelennek (kártya nézetek és részletező modalok egyaránt).
- Nincs új adatmodell-mező, nincs Google Sheet séma változás — a meglévő szabadszöveges mezőkbe írt URL válik kattinthatóvá.
- A linkify implementáció nem engedhet tetszőleges HTML/attribútum befecskendezést a felismert URL értékén keresztül (pl. a felismert URL-t nem escape-eletlenül helyezzük a `href` attribútumba).
- Mindkét érintett fájlban (`index_5a.html`, `index_7a.html`) azonos módon valósul meg.

Nem változik:
- A meglévő, szélesebb körű HTML-escapelés hiánya a leírás-mezőkben (ez külön, ezen a changen kívül eső téma).
- Az adatmodell (`documents`, `h.desc`/`h.note` mezők) szerkezete.

## Capabilities

### New Capabilities

- `url-linkify`: Szabadszöveges leírás-mezőkben (házi feladat leírás/megjegyzés, dokumentum leírás) megjelenő `http(s)://` URL-ek automatikusan kattintható linkként jelennek meg, biztonságosan (HTML/attribútum-injektálás nélkül).

### Modified Capabilities

_(nincs — nincs meglévő spec-capability a projektben, amit ez módosítana)_

## Impact

- `index_5a.html` — a házi feladat leírás/megjegyzés renderelő helyei (kártya- és listanézet, részletező modal) és a Dokumentumok tab `docCardHTML()`/`openDocDetail()` renderelői érintettek, plusz egy új, megosztott linkify segédfüggvény.
- `index_7a.html` — ugyanazok a helyek, azonos módosítással (kb. `index_7a.html:1129, 1207, 1225, 2035` a házi feladatoknál, `index_7a.html:2432-2492` a Dokumentumok tabnál; `index_5a.html`-ben hasonló, kis eltolással).
- Nincs API, adatbázis vagy build-folyamat érintve.
