# Házi Feladatok – Osztály Feladatkezelő

Mobil-barát webalkalmazás általános iskolai osztályok házi feladatainak és dokumentumainak közös kezelésére. Google Sheets az adatbázis, Google Apps Script a backend, egyetlen HTML fájl a frontend – telepítés nélkül használható.

## Verziók

| Fájl | Osztály | Cloudinary mappa |
|------|---------|-----------------|
| `index_5a.html` | 5.a | `hazik_5a` |
| `index_7a.html` | 7.a | `hazik_7a` |

## Funkciók

- **Feladatok** — házi feladat feltöltés képekkel, határidővel, típussal (témazáró, dolgozat, projekt, órai anyag)
- **Rendezés** — határidő szerint (alapértelmezett) vagy feltöltés szerint; preferencia megmarad
- **Csoportos nézet** — feladatok szekciókban: Ma & Holnap / Ezen a héten / Később / Lejárt
- **Alapértelmezett határidő** — ha nem töltik ki, automatikusan feltöltés + 7 nap
- **Naptár** — iskolai események és dolgozatok naptárban
- **Dokumentumok** — osztályanyagok, linkek, fájlok könyvtára
- **Értesítők** — Messenger / WhatsApp / Telegram üzenet generálás hiányzó feladathoz
- **Kuka** — törölt feladatok visszaállítása 30 napig
- **Kedvencek** — csillagozott feladatok
- **Keresés és szűrés** — tantárgy, típus, dátumtartomány, szabad szöveges keresés
- **Nyomtatás** — feladatkártyák és képek nyomtatható nézetben
- **Kijelölés** — több feladat egyszerre törlése / mozgatása (hosszú nyomás mobilon)

## Technológiai stack

```
Frontend:  HTML + CSS + Vanilla JS (egyetlen fájl, build nélkül)
Backend:   Google Apps Script (apps_script.gs) → Google Sheets
Képtárhely: Cloudinary (ingyenes tier)
Auth:      Google OAuth (Apps Script web app)
```

## Telepítés

### 1. Google Sheets előkészítése

Hozz létre egy Google Spreadsheet-et. A szükséges lapokat az Apps Script automatikusan létrehozza az első futáskor:
- `Config` — beállítások (osztály neve, aktív tanév, tantárgyak)
- `Feladatok_ÉÉÉV-ÉÉÉÉ` — feladatok tanévenként
- `Dokumentumok_ÉÉÉV-ÉÉÉÉ` — dokumentumok tanévenként
- `Kuka`, `Kedvencek`, `Naptár`, stb.

### 2. Google Apps Script telepítése

1. Nyisd meg a Spreadsheet-et → **Bővítmények → Apps Script**
2. Másold be az `apps_script.gs` tartalmát
3. **Telepítés → Webalkalmazásként** — Hozzáférés: *Mindenki*
4. Másold ki a webalkalmazás URL-jét

### 3. Cloudinary fiók

Hozz létre ingyenes fiókot a [cloudinary.com](https://cloudinary.com) oldalon, és jegyezd fel:
- Cloud name
- Unsigned upload preset neve (hozd létre a Settings → Upload menüben)

### 4. HTML konfiguráció

Nyisd meg az osztályodnak megfelelő HTML fájlt, és töltsd ki a `CFG` objektumot a fájl elejénél (~375. sor):

```js
const CFG = {
  CNAME:         '5.a osztaly',        // Osztály neve (megjelenik a fejlécben)
  PIN:           '2026',               // Belépési PIN
  SHEET_ID:      'A_SPREADSHEET_ID',   // Google Sheets ID az URL-ből
  SCRIPT_URL:    'AZ_APPS_SCRIPT_URL', // Webalkalmazás URL
  CLOUD_NAME:    'cloudinary_neve',    // Cloudinary cloud name
  UPLOAD_PRESET: 'preset_neve',        // Cloudinary upload preset
  CLOUD_FOLDER:  'hazik_5a',           // Cloudinary mappa neve
};
```

### 5. Közzététel

A HTML fájlt bármelyik statikus hosting szolgáltatóra feltöltheted (GitHub Pages, Netlify, Google Sites, stb.), vagy egyszerűen megnyithatod helyben böngészőből is.

## Config Sheet beállítások

Az Apps Script a `Config` lapon tárolt kulcs-érték párokat olvassa:

| Kulcs | Példa | Leírás |
|-------|-------|--------|
| `osztaly_nev` | `SZEKAI 7. a osztály` | Megjelenik a fejlécben |
| `aktiv_tanev` | `2026-2027` | Aktív tanév |
| `tanevek` | `2025-2026,2026-2027` | Elérhető tanévek |
| `tantargyak_2026-2027` | `Magyar,Matek,Fizika,…` | Tantárgyak az adott tanévhez |

## Fejlesztés

Mindkét HTML fájl önálló — nincs build rendszer, nincs csomagkezelő. Szerkesztés után egyszerűen töltsd fel a hosting-ra.

A tervezési és fejlesztési dokumentáció az `openspec/` mappában található (OpenSpec változáskövetés).
