# Design

## Context

`index_5a.html` és `index_7a.html` két külön, egymástól független, egyfájlos HTML/JS alkalmazás (nincs közös modul vagy build-lépés közöttük — korábbi változtatásoknál is mindkét fájlt párhuzamosan kellett szerkeszteni). A leírás-mezők (`h.desc`, `h.note`, `d.desc`) jelenleg escapelés nélkül, nyers template string-ként kerülnek `innerHTML`-be számos renderelő helyen. Lásd proposal.md - Why.

## Goals / Non-Goals

**Goals:**
- Egy kis, önálló segédfüggvény, ami egy szöveges bemenetet biztonságosan HTML-escape-el, majd az escapelt szövegben a `http(s)://` mintákat `<a>` taggé alakítja.
- Ugyanez a függvény (kódmásolatban, mindkét fájlban) hívódik minden olyan helyen, ahol `h.desc`, `h.note` vagy `d.desc` megjelenik.

**Non-Goals:**
- Nem vezetünk be általános HTML-escapelést minden egyéb mezőre (pl. `title`, `tags`) — ez explicit nem célja ennek a change-nek.
- Nem hozunk létre közös/megosztott JS fájlt a két HTML app között — megmarad a jelenlegi, fájlonként duplikált minta.
- Nem adunk hozzá dedikált "link" adatmodell-mezőt (ld. proposal.md).

## Decisions

**1. Escape + linkify egy lépésben, egy segédfüggvényben (`linkifyDesc(text)`)**
A függvény előbb HTML-escape-eli a teljes bemenetet (`&`, `<`, `>`, `"`, `'`), majd egy regexpel (`/(https?:\/\/[^\s<>"']+)/g`) megkeresi az escapelt szövegben maradt URL-mintákat, és minden találatot `<a href="<escapelt-url>" target="_blank" rel="noopener">` taggé cserél, ahol a linkszöveg maga az URL.
- *Miért ez, és nem egy külön `escapeHtml` + külön `linkify` lépés?* Mert a sorrend fontos: ha előbb linkify fut a nyers szövegen, majd escape a teljes eredményen, az escape lerombolja a frissen beszúrt `<a href>` tag jeleit. Az escape-first sorrend garantálja, hogy a felhasználó szövegéből soha nem kerülhet be nyers `<`, `>`, `"` karakter az `href` attribútumba vagy a kimeneti HTML-be — ez zárja ki az attribútum-injektálást (ld. spec: Biztonságos linkesítés).
- *Alternatíva*: DOM-alapú `textContent` + `createElement('a')` építés sablonstring helyett. Elvetve: a kódbázis mindenhol template string + `innerHTML` mintát követ, ez az egyetlen hely ahol DOM-építésre váltani inkonzisztens lenne és nagyobb diffet okozna a célnál.

**2. A regex csak `http://`/`https://` prefixű URL-eket ismer fel**
Nem próbálunk "www."-vel kezdődő vagy protokoll nélküli mintákat is felismerni — ez a kért használati eset (teljes URL bemásolása) szempontjából elég, és elkerüli a hamis pozitívokat (pl. fájlnevek, pontozott szövegek).

**3. Kódduplikáció mindkét fájlban, nem megosztott snippet**
A `linkifyDesc()` függvényt szó szerint ugyanazzal a testtel kell bemásolni `index_5a.html`-be és `index_7a.html`-be, ugyanúgy, ahogy a korábbi `cancelTemplate()` javítás is mindkét fájlban külön történt. Ez illeszkedik a projekt jelenlegi, nem-DRY, de egyszerű deploy-modelljéhez (statikus HTML fájlok, nincs build lépés, ami összefésülné őket).

## Risks / Trade-offs

- **[Risk]** Egy agresszív regex véletlenül "elharapja" a mondat záró írásjelét (pl. a mondatvégi pontot az URL részeként kezeli) → **Mitigáció**: a regex kizárja a whitespace-t és a `<>"'` karaktereket a találatból, de nem zárja ki explicit a záró írásjeleket (`.`, `,`, `)`); ez ismert, elfogadott apró korlát — a felhasználó jellemzően külön sorban/végén illeszti be a linket, ahogy a megbeszélt használati eset (dokumentum leírás = maga a link) is mutatja.
- **[Risk]** A duplikált segédfüggvény később szétcsúszhat a két fájl között, ha csak az egyikben javítanak egy hibát → **Mitigáció**: nincs azonnali technikai mitigáció (nincs közös modul), ez a projekt létező, elfogadott duplikációs mintájának a folytatása, nem új kockázat.
