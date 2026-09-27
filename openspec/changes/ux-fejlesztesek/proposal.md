# Proposal

## Why

Az alkalmazás funkcionálisan helyes, de néhány kisebb UX finomítással jelentősen gyorsabb és vizuálisan érthetőbb lenne mobilon. A tanulók a legfontosabb kérdést — "mit kell még megcsinálnom?" — jelenleg nem tudják személyesen jelölni, az új feladat form dátummezője mindig üres, és a sürgős feladatok nem emelkednek ki elég határozottan.

## What Changes

- **"Megcsináltam" checkbox**: személyes pipálás kártyánként, localStorage-ban tárolva. A kész kártyák elhalványulnak és a lista aljára kerülnek. Más felhasználók állapotát nem érinti.
- **Due date előre kitöltve**: új feladat form megnyitásakor a határidő mező automatikusan holnap dátumát mutatja (szerkesztésnél változatlan).
- **Sürgős sticky sáv**: ha van ma vagy holnap esedékes aktív feladat, a lista felett egy tapintható sáv jelenik meg a legközelebbi ilyen feladattal; tapra a kártyára ugrik.
- **Tantárgy szín kódolás**: minden tantárgyhoz konzisztens szín rendelődik (hash-alapú, a tantárgy nevéből számítva). A kártyán bal oldali szín csík jelzi — a típus-alapú szín csík mellé második rétegként.
- **Tab urgencia badge**: ha van ma esedékes feladat, a Feladatok tab szövege után `🔴` jelenik meg.
- Mindkét fájlra alkalmazandó: `index_5a.html` és `index_7a.html`.

## Capabilities

### New Capabilities

- `szemelyes-allapot`: Személyes "megcsináltam" jelölés localStorage-ban, megjelenítése a kártyákon.
- `ux-kiemelések`: Sürgős sticky sáv, tantárgy szín kódolás, tab urgencia badge, due date előtöltés.

### Modified Capabilities

*(nincs meglévő archivált spec)*

## Impact

- `index_5a.html`, `index_7a.html`: frontend JS és CSS módosítások
- localStorage kulcsok: `hz_done_5a` / `hz_done_7a` (megcsináltam állapotok JSON set)
- Google Sheets: nem változik
