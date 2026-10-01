#!/usr/bin/env python3.11
"""
Kréta órarend letöltő – webes felület + Excel export
Telepítés: pip3.11 install flask beautifulsoup4 requests openpyxl
Futtatás:  ./kreta_orarend.py
"""

import io
import json
import re
import zipfile
import threading
import webbrowser
from datetime import date, timedelta, datetime
from pathlib import Path
from time import sleep

import requests
from bs4 import BeautifulSoup as bs
from flask import Flask, jsonify, render_template_string, request, send_file

CONFIG_FILE = Path(__file__).parent / "kreta_config.json"
SESSIONS_DIR = Path(__file__).parent / ".kreta_sessions"

# In-memory session cache (survives within one server run)
_session_cache: dict[str, requests.Session] = {}

def _session_file(school_code: str, username: str) -> Path:
    safe = f"{school_code}_{username}".replace("/", "_")
    return SESSIONS_DIR / f"{safe}.json"

def _save_session(sess: requests.Session, school_code: str, username: str) -> None:
    SESSIONS_DIR.mkdir(exist_ok=True)
    cookies = {c.name: {"value": c.value, "domain": c.domain, "path": c.path}
               for c in sess.cookies}
    _session_file(school_code, username).write_text(json.dumps(cookies))

def _load_session(school_code: str, username: str) -> requests.Session | None:
    f = _session_file(school_code, username)
    if not f.exists():
        return None
    try:
        data = json.loads(f.read_text())
        sess = requests.Session()
        for name, info in data.items():
            sess.cookies.set(name, info["value"], domain=info.get("domain"), path=info.get("path"))
        return sess
    except Exception:
        return None

def get_cached_session(school_code: str, username: str, password: str) -> requests.Session:
    key = f"{school_code}|{username}"
    base = f"https://{school_code}.e-kreta.hu"

    def _is_alive(sess: requests.Session) -> bool:
        try:
            r = sess.get(f"{base}/Tanulo/TanuloHaziFeladat", allow_redirects=False, timeout=8)
            loc = r.headers.get("Location", "")
            return r.status_code == 200 or (r.status_code in (301, 302) and "Login" not in loc)
        except Exception:
            return False

    # 1. In-memory cache
    sess = _session_cache.get(key)
    if sess and _is_alive(sess):
        return sess

    # 2. Persisted cookies from disk (avoids re-login after server restart)
    sess = _load_session(school_code, username)
    if sess and _is_alive(sess):
        _session_cache[key] = sess
        return sess

    # 3. Full re-login
    sess = web_login(school_code, username, password)
    _session_cache[key] = sess
    _save_session(sess, school_code, username)
    return sess

NAP_HU   = {0: "hetfo", 1: "kedd", 2: "szerda", 3: "csutortok", 4: "pentek"}
NAP_NEVO = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek"]

PALETTA = [
    "#1a56db","#7e3af2","#e74694","#e3a008","#057a55",
    "#d03801","#0694a2","#3f83f8","#9061f9","#f05252",
    "#ff8800","#31c48d","#c27803","#6875f5","#76e3ea",
    "#84cc16","#f97316","#ec4899","#14b8a6","#8b5cf6",
]

def targy_szin_map(napok: dict) -> dict[str, str]:
    """Tárgyankénti egységes szín – sorrend: első előfordulás."""
    seen: list[str] = []
    for nap in ["hetfo", "kedd", "szerda", "csutortok", "pentek"]:
        for ora in napok.get(nap, []):
            t = ora["targy"]
            if t not in seen:
                seen.append(t)
    return {t: PALETTA[i % len(PALETTA)] for i, t in enumerate(seen)}

NORMALIZALAS = {
    "református hittan": "Hittan",
    "katolikus hittan":  "Hittan",
    "etika":             "Hittan",
    "erkölcstan":        "Hittan",
}

# ── Config ───────────────────────────────────────────────────────────────────

def load_config() -> list:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []

def save_config(profiles: list):
    CONFIG_FILE.write_text(json.dumps(profiles, indent=2, ensure_ascii=False), encoding="utf-8")

# ── Kréta ────────────────────────────────────────────────────────────────────

def normalizal(nev: str) -> str:
    k = nev.strip().lower()
    for kulcs, ertek in NORMALIZALAS.items():
        if kulcs in k:
            return ertek
    return nev.strip()

def parse_title(title: str) -> tuple[str, str]:
    """title = 'Tantárgy\nTanár neve\n(terem)' → (tanár, terem)"""
    lines = [l.strip() for l in (title or "").split("\n") if l.strip()]
    tanar = lines[1] if len(lines) > 1 else ""
    terem = lines[2].strip("()") if len(lines) > 2 else ""
    return tanar, terem

def web_login(school_code: str, username: str, password: str) -> requests.Session:
    base = f"https://{school_code}.e-kreta.hu"
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})

    resp = session.get(f"{base}/", allow_redirects=True)
    soup = bs(resp.text, "html.parser")
    rvt = soup.find("input", {"name": "__RequestVerificationToken"})
    return_url = soup.find("input", {"name": "ReturnUrl"})
    if not rvt or not return_url:
        raise Exception("Nem sikerült az IDP login oldalt betölteni")

    sleep(0.5)
    login_resp = session.post(
        "https://idp.e-kreta.hu/account/login",
        data={"UserName": username, "Password": password,
              "ReturnUrl": return_url["value"], "__RequestVerificationToken": rvt["value"],
              "IsTemporaryLogin": "false", "loginType": "InstituteLogin", "InstituteCode": school_code},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        allow_redirects=True,
    )
    form = bs(login_resp.text, "html.parser").find("form")
    if not form:
        raise Exception("Bejelentkezés sikertelen – ellenőrizd a jelszót és az iskola kódot!")

    inputs = {i.get("name"): i.get("value", "") for i in form.find_all("input")}
    final = session.post(form.get("action", base), data=inputs, allow_redirects=True)
    if "e-kreta.hu" not in final.url or "Login" in final.url:
        raise Exception("Visszairányítás sikertelen – ellenőrizd a jelszót!")
    return session


def get_tanulo_id(html: str) -> str:
    for pattern in [
        r'[Tt]anuloId["\']?\s*[:=]\s*["\']?(\d+)',
        r'data-tanulo-id=["\'](\d+)["\']',
        r'"TanuloId"\s*:\s*(\d+)',
    ]:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def get_tanev_headers(session: requests.Session, base: str) -> dict:
    """Fetch the házi feladat page and extract tanév selection headers."""
    try:
        resp = session.get(f"{base}/Tanulo/TanuloHaziFeladat", allow_redirects=True, timeout=15)
        html = resp.text
        tanev_id = tanev_sorsz = tanev_nev = None
        for pattern in [
            r'"selectedTanevId"\s*:\s*(\d+)',
            r'selectedTanevId\s*=\s*(\d+)',
            r'data-tanev-id=["\'](\d+)["\']',
            r'TanevId["\']?\s*:\s*(\d+)',
        ]:
            m = re.search(pattern, html, re.IGNORECASE)
            if m:
                tanev_id = m.group(1)
                break
        for pattern in [
            r'"selectedTanevSorszam"\s*:\s*(\d+)',
            r'selectedTanevSorszam\s*=\s*(\d+)',
            r'TanevSorszam["\']?\s*:\s*(\d+)',
        ]:
            m = re.search(pattern, html, re.IGNORECASE)
            if m:
                tanev_sorsz = m.group(1)
                break
        for pattern in [
            r'"selectedTanevNev"\s*:\s*"([^"]+)"',
            r'selectedTanevNev\s*=\s*["\']([^"\']+)["\']',
            r'TanevNev["\']?\s*:\s*["\']([^"\']+)["\']',
            r'(\d{4}/\d{4})',
        ]:
            m = re.search(pattern, html, re.IGNORECASE)
            if m:
                tanev_nev = m.group(1)
                break
        # Fallback: check session cookies for TanevId
        if not tanev_id:
            for cname in ["SelectedTanevId", "selectedTanevId", "TanevId", "tanev_id"]:
                cval = session.cookies.get(cname)
                if cval and str(cval).isdigit():
                    tanev_id = str(cval)
                    break
        hdrs = {}
        if tanev_id:
            hdrs["X-Selected-TanevId"] = tanev_id
        if tanev_sorsz:
            hdrs["X-Selected-TanevSorszam"] = tanev_sorsz
        if tanev_nev:
            hdrs["X-Selected-TanevNev"] = tanev_nev
        tanulo_id = get_tanulo_id(html)
        if tanulo_id:
            hdrs["_TanuloId"] = tanulo_id
        return hdrs
    except Exception as e:
        app.logger.error(f"get_tanev_headers error: {e}")
        return {}


def fetch_hazifeladatok_all(school_code: str, username: str, password: str,
                             logs: list | None = None) -> dict:
    if logs is None:
        logs = []
    def log(msg): logs.append(msg)

    base = f"https://{school_code}.e-kreta.hu"
    log(f"Session ellenőrzés... ({username} @ {school_code})")
    session = get_cached_session(school_code, username, password)
    log("Session OK.")

    tanev_hdrs = get_tanev_headers(session, base)
    if tanev_hdrs:
        log(f"Tanév: {tanev_hdrs.get('X-Selected-TanevNev','?')} (id={tanev_hdrs.get('X-Selected-TanevId','?')})")
    else:
        log("Figyelem: tanév fejlécek nem találhatók, próbálkozás fejlécek nélkül.")

    req_hdrs = {**tanev_hdrs, "X-Requested-With": "XMLHttpRequest", "Accept": "application/json"}

    import json as _json
    log("Házi feladatok lekérése...")
    resp = session.get(
        f"{base}/api/TanuloHaziFeladatApi/GetTanulotHaziFeladatGrid",
        params={
            "sort": "HaziFeladatHatarido-asc",
            "page": "1",
            "pageSize": "100",
            "group": "",
            "filter": "",
            "data": _json.dumps({"RegiHaziFeladatokElrejtese": False}),
        },
        headers=req_hdrs,
    )
    if not resp.ok:
        log(f"API hiba {resp.status_code}: {resp.text[:400]}")
        resp.raise_for_status()

    raw = resp.json()
    hazi_lista = raw.get("Data", raw) if isinstance(raw, dict) else raw
    log(f"{len(hazi_lista)} házi feladat találva.")
    if hazi_lista:
        log(f"[debug] 1. item mezők: {list(hazi_lista[0].keys())}")
        log(f"[debug] HaziFeladatId={hazi_lista[0].get('HaziFeladatId')}, ID={hazi_lista[0].get('ID')}")

    tanulo_id = tanev_hdrs.get("_TanuloId", "")
    # Fallback: try to get TanuloId from the homework list items themselves
    if not tanulo_id and hazi_lista:
        for field in ["TanuloId", "tanuloId", "Tanuloid"]:
            v = hazi_lista[0].get(field)
            if v:
                tanulo_id = str(v)
                break
    log(f"TanuloId: {tanulo_id or 'NEM TALÁLTUNK – csonkított szövegek maradnak'}")

    truncated = 0
    for hf in hazi_lista:
        hf_id = hf.get("HaziFeladatId") or hf.get("ID")
        event_id = hf.get("EventId") or hf.get("TanitasiOraId", "")  # calendar event ID for tab
        szoveg = hf.get("HaziFeladatSzoveg", "") or ""

        # Fetch full text from detail tab if we have the calendar event ID
        if event_id and tanulo_id:
            ora_datum = hf.get("OraDatuma", "")
            try:
                # Convert ISO date to Kréta format: "2026. 09. 18. 0:00:00"
                from datetime import datetime as _dt
                d = _dt.fromisoformat(ora_datum[:19])
                date_str = d.strftime("%-Y. %m. %d. %-H:%M:%S")
            except Exception:
                date_str = ora_datum
            megoldva = "T" if hf.get("MegoldottHF_BOOL") else "F"
            tab_resp = session.get(
                f"{base}/Orarend/InformaciokOrarend/GetHaziFeladat_Tab",
                params={"Id": event_id, "EventType": 2, "Date": date_str,
                        "TanuloId": tanulo_id, "Megoldva": megoldva},
                headers={"X-Requested-With": "XMLHttpRequest",
                         "Referer": f"{base}/Orarend/InformaciokOrarend"},
            )
            if tab_resp.ok and tab_resp.text.strip():
                soup = bs(tab_resp.text, "html.parser")
                # Remove script/style noise, then grab the longest text block
                for tag in soup(["script", "style", "button", "a"]):
                    tag.decompose()
                best = ""
                for sel in [".hazifeladat-szoveg", "p.hazi-leiras", "div.leiras",
                             "p", "div.content", "td", "div"]:
                    for el in soup.select(sel):
                        t = el.get_text(" ", strip=True)
                        if len(t) > len(best):
                            best = t
                if best and len(best) >= len(szoveg):
                    hf["HaziFeladatSzoveg"] = best
                    truncated += 1
            sleep(0.1)

        if not hf_id:
            hf["_Csatolmanyok"] = []
            continue
        cs_resp = session.get(
            f"{base}/api/InformaciokOrarendApi/GetHFCsatolmanyokGridForHazi",
            params={
                "haziFeladatId": hf_id,
                "sort": "FeltoltesDatum-asc",
                "page": "1",
                "pageSize": "100",
                "group": "",
                "filter": "",
                "data": "{}",
            },
            headers=req_hdrs,
        )
        if cs_resp.ok:
            cs_raw = cs_resp.json()
            cs_list = cs_raw.get("Data", cs_raw) if isinstance(cs_raw, dict) else cs_raw
            hf["_Csatolmanyok"] = cs_list if isinstance(cs_list, list) else []
            if hf["_Csatolmanyok"]:
                log(f"  {hf.get('TantargyNev','?')}: {len(hf['_Csatolmanyok'])} melléklet")
        else:
            hf["_Csatolmanyok"] = []
            log(f"  Melléklet API hiba: {cs_resp.status_code} (haziFeladatId={hf_id})")
        sleep(0.1)

    if truncated:
        log(f"{truncated} feladatnál teljes szöveget töltöttük le.")
    total_cs = sum(len(hf.get("_Csatolmanyok", [])) for hf in hazi_lista)
    log(f"Összesen {total_cs} melléklet.")
    return {"hazi_lista": hazi_lista, "logs": logs}


def fetch_orarend(school_code: str, username: str, password: str, hetek: int,
                  logs: list | None = None) -> dict:
    if logs is None:
        logs = []
    def log(msg): logs.append(msg)

    base = f"https://{school_code}.e-kreta.hu"
    log(f"Bejelentkezés... ({username} @ {school_code})")
    session = web_login(school_code, username, password)
    log("Sikeres bejelentkezés.")

    hdrs = {"X-Requested-With": "XMLHttpRequest", "Accept": "application/json",
            "Referer": f"{base}/Orarend/InformaciokOrarend"}

    ma = date.today()
    het_eleje = ma - timedelta(days=ma.weekday())

    # nap → { oraszam → [ora_dict, ...] }  (több hét átlagoláshoz)
    napok_raw: dict[str, dict[int, list[dict]]] = {}

    for het in range(hetek):
        eleje = het_eleje + timedelta(weeks=het)
        vege  = eleje + timedelta(days=6)
        log(f"Lekérés: {eleje} – {vege}")

        resp = session.get(
            f"{base}/api/CalendarApi/GetTanuloOrarend",
            params={"start": eleje.isoformat(), "end": vege.isoformat(),
                    "tanuloId": -1, "tanarId": -1, "osztalyCsoportId": -1, "teremId": -1},
            headers=hdrs,
        )
        if not resp.ok:
            log(f"API hiba {resp.status_code}: {resp.text[:400]}")
            resp.raise_for_status()

        orak = resp.json()
        log(f"  {len(orak)} óra megtalálva")

        for ora in orak:
            if ora.get("Torolt") or ora.get("isElmaradt"):
                continue
            datum_str = ora.get("start") or ora.get("datum") or ""
            if not datum_str:
                continue
            try:
                nap_idx = date.fromisoformat(datum_str[:10]).weekday()
            except ValueError:
                continue
            nap_key = NAP_HU.get(nap_idx)
            if nap_key is None:
                continue

            hanyadik = ora.get("hanyadikora") or 0
            tanar, terem = parse_title(ora.get("title", ""))
            napok_raw.setdefault(nap_key, {}).setdefault(hanyadik, []).append({
                "targy":     normalizal(str(ora.get("Tantargy") or "?")),
                "tol":       datum_str[11:16],
                "ig":        (ora.get("end") or "")[:16][11:],
                "tanar":     tanar,
                "terem":     terem,
                "hanyadik":  hanyadik,
                "oraszam":   ora.get("oraszam") or f"{hanyadik}. óra",
                "color":     ora.get("color") or "#94a3b8",
                "hetirend":  ora.get("hetirend") or "",
            })

    # Összesít: minden nap, minden óra → leggyakoribb tárgy
    napok: dict[str, list[dict]] = {}
    for nap_key, orak_by_szam in sorted(napok_raw.items()):
        orak_lista = []
        for hanyadik, pelda_lista in sorted(orak_by_szam.items()):
            # leggyakoribb példányt vesszük
            best = max(pelda_lista, key=lambda x: pelda_lista.count(x))
            orak_lista.append(best)
        napok[nap_key] = orak_lista

    # Config sheet kimenet
    config_sorok = []
    for nap in ["hetfo", "kedd", "szerda", "csutortok", "pentek"]:
        orak_lista = napok.get(nap, [])
        if not orak_lista:
            continue
        seen, targyak = [], []
        for o in orak_lista:
            if o["targy"] not in seen:
                seen.append(o["targy"])
                ido = f"@{o['tol']}–{o['ig']}" if o.get("tol") else ""
                targyak.append(f"{o['targy']}{ido}")
        config_sorok.append(f"orarend_{nap}\t{' | '.join(targyak)}")

    szinek = targy_szin_map(napok)
    return {"config": "\n".join(config_sorok), "napok": napok, "szinek": szinek, "logs": logs}


# ── Excel export ──────────────────────────────────────────────────────────────

def build_excel(napok: dict, profile_name: str, szinek: dict | None = None) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Órarend"

    thin = Side(border_style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    nap_keys = ["hetfo", "kedd", "szerda", "csutortok", "pentek"]

    # Max óra szám
    max_ora = max((len(napok.get(n, [])) for n in nap_keys), default=0)

    # Fejléc sor – napok
    ws.cell(1, 1, "").fill = PatternFill("solid", fgColor="1a56db")
    for col, nev in enumerate(NAP_NEVO, start=2):
        c = ws.cell(1, col, nev)
        c.font = Font(bold=True, color="FFFFFF", size=12)
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.fill = PatternFill("solid", fgColor="1a56db")
        c.border = border
        ws.column_dimensions[get_column_letter(col)].width = 26

    ws.column_dimensions["A"].width = 10
    ws.row_dimensions[1].height = 28

    # Összegyűjtjük az összes órát nap+hanyadik szerint
    grid: dict[tuple[str, int], dict] = {}
    for nap_key in nap_keys:
        for ora in napok.get(nap_key, []):
            grid[(nap_key, ora["hanyadik"])] = ora

    hanyadikok = sorted({ora["hanyadik"] for orak in napok.values() for ora in orak})

    for row_idx, hanyadik in enumerate(hanyadikok, start=2):
        ws.row_dimensions[row_idx].height = 56

        # Óra sorszám oszlop
        c = ws.cell(row_idx, 1, f"{hanyadik}.\nóra")
        c.font = Font(bold=True, size=10, color="374151")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.fill = PatternFill("solid", fgColor="F1F5F9")
        c.border = border

        for col_idx, nap_key in enumerate(nap_keys, start=2):
            ora = grid.get((nap_key, hanyadik))
            c = ws.cell(row_idx, col_idx)
            c.border = border
            c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

            if ora:
                szin_raw = (szinek or {}).get(ora["targy"]) or ora.get("color") or "#94a3b8"
                hex_color = szin_raw.lstrip("#")
                # Halványított háttér (mix fehérrel)
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                r2 = int(r * 0.25 + 255 * 0.75)
                g2 = int(g * 0.25 + 255 * 0.75)
                b2 = int(b * 0.25 + 255 * 0.75)
                bg = f"{r2:02X}{g2:02X}{b2:02X}"
                c.fill = PatternFill("solid", fgColor=bg)

                tanar_sor = f"\n👤 {ora['tanar']}" if ora["tanar"] else ""
                terem_sor = f"  🚪 {ora['terem']}" if ora["terem"] else ""
                idopont = f"⏰ {ora['tol']}–{ora['ig']}" if ora["tol"] else ""

                c.value = f"📚 {ora['targy']}\n{idopont}{tanar_sor}{terem_sor}"
                c.font = Font(size=10, color=hex_color)
            else:
                c.fill = PatternFill("solid", fgColor="F8FAFC")

    # Cím
    ws.insert_rows(1)
    ws.merge_cells("A1:F1")
    title_cell = ws.cell(1, 1, f"Órarend – {profile_name}")
    title_cell.font = Font(bold=True, size=14, color="1a56db")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    title_cell.fill = PatternFill("solid", fgColor="EFF6FF")
    ws.row_dimensions[1].height = 32

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# ── Flask ─────────────────────────────────────────────────────────────────────

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="hu">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kréta Órarend</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,sans-serif;background:#f0f4f8;padding:20px 12px}
h1{font-size:20px;font-weight:800;color:#1a56db;margin-bottom:20px;text-align:center}
.card{background:#fff;border-radius:14px;box-shadow:0 2px 8px #0001;padding:20px;margin-bottom:16px;max-width:960px;margin-left:auto;margin-right:auto}
label{font-size:12px;font-weight:700;color:#555;display:block;margin-bottom:4px;margin-top:12px}
input{width:100%;padding:10px 12px;border:2px solid #e0e7ef;border-radius:9px;font-size:15px;outline:none;transition:border .15s}
input:focus{border-color:#1a56db}
.row{display:flex;gap:8px;margin-top:16px;flex-wrap:wrap}
button{flex:1;padding:11px;border:none;border-radius:9px;font-size:14px;font-weight:700;cursor:pointer;transition:opacity .15s;min-width:120px}
button:active{opacity:.75}
.btn-primary{background:#1a56db;color:#fff}
.btn-secondary{background:#e0e7ef;color:#374151}
.btn-danger{background:#fee2e2;color:#dc2626}
.btn-green{background:#d1fae5;color:#065f46}
.btn-excel{background:#217346;color:#fff}
#log{background:#1e293b;color:#94a3b8;border-radius:9px;padding:12px;font-size:12px;font-family:monospace;white-space:pre-wrap;max-height:160px;overflow-y:auto;margin-top:12px;display:none}
.profile-row{display:flex;align-items:center;gap:8px;padding:10px 12px;border:2px solid #e0e7ef;border-radius:9px;margin-bottom:8px;cursor:pointer;transition:border .15s}
.profile-row:hover,.profile-row.active{border-color:#1a56db;background:#eff6ff}
.profile-name{font-weight:700;font-size:14px;flex:1}
.profile-sub{font-size:11px;color:#888}
.section-title{font-size:13px;font-weight:800;color:#374151;margin-bottom:10px}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin .6s linear infinite;vertical-align:middle;margin-right:6px}
@keyframes spin{to{transform:rotate(360deg)}}

/* Timetable */
.tt-wrap{overflow-x:auto;margin-top:12px}
table.tt{border-collapse:collapse;width:100%;min-width:600px}
table.tt th{background:#1a56db;color:#fff;padding:10px 8px;font-size:13px;text-align:center;font-weight:700;position:sticky;top:0}
table.tt th:first-child{width:52px}
table.tt td{border:1px solid #e0e7ef;padding:0;vertical-align:top;min-width:120px}
table.tt td.ora-num{background:#f1f5f9;text-align:center;font-weight:700;font-size:12px;color:#64748b;padding:6px 4px;vertical-align:middle}
.ora-cell{padding:8px;min-height:72px;height:100%}
.ora-targy{font-weight:700;font-size:13px;margin-bottom:3px}
.ora-time{font-size:11px;color:#64748b;margin-bottom:2px}
.ora-tanar{font-size:11px;color:#475569}
.ora-terem{font-size:11px;color:#94a3b8}
.empty-cell{background:#f8fafc}

/* Config output */
#configOut{background:#f8fafc;border:2px solid #e0e7ef;border-radius:9px;padding:12px;font-size:13px;font-family:monospace;white-space:pre;margin-top:8px;display:none}
</style>
</head>
<body>
<h1>🎓 Kréta Órarend Letöltő</h1>

<div class="card">
  <div class="section-title">Profilok</div>
  <div id="profileList"></div>
  <button class="btn-secondary" style="margin-top:8px;width:100%" onclick="newProfile()">+ Új profil</button>
</div>

<div class="card" id="editCard" style="display:none">
  <div class="section-title" id="editTitle">Profil</div>
  <label>Profil neve</label><input id="f_name" placeholder="7.a – Géza">
  <label>Iskola kód (URL előtag)</label><input id="f_school" placeholder="szenterzsebet">
  <label>Felhasználónév</label><input id="f_user" placeholder="73295157638G01">
  <label>Jelszó</label><input id="f_pass" type="password" placeholder="••••••">
  <label>Hetek száma</label><input id="f_hetek" type="number" value="2" min="1" max="6">
  <div class="row">
    <button class="btn-primary" onclick="saveProfile()">💾 Mentés</button>
    <button class="btn-secondary" onclick="cancelEdit()">Mégsem</button>
    <button class="btn-danger" id="deleteBtn" onclick="deleteProfile()" style="display:none">Törlés</button>
  </div>
</div>

<div class="card" id="fetchCard" style="display:none">
  <div class="section-title">Letöltés – <span id="selectedLabel"></span></div>
  <div class="row">
    <button class="btn-primary" id="fetchBtn" onclick="doFetch()">⬇ Órarend letöltése</button>
  </div>
  <div class="row" style="margin-top:8px">
    <button class="btn-secondary" id="haziBtn" onclick="doFetchHazi()" style="display:none">📚 Házi feladatok letöltése</button>
  </div>
  <div id="log"></div>
</div>

<div class="card" id="resultCard" style="display:none">
  <div class="section-title">Órarend</div>
  <div class="row" style="margin-bottom:12px">
    <button class="btn-excel" onclick="downloadExcel()">📊 Excel letöltése</button>
    <button class="btn-green" onclick="copyConfig()">📋 Config másolás</button>
  </div>
  <div class="tt-wrap"><table class="tt" id="ttTable"></table></div>
  <div style="margin-top:16px;font-size:12px;font-weight:700;color:#555">Config sheet sorok:</div>
  <div id="configOut"></div>
</div>

<div class="card" id="haziCard" style="display:none">
  <div class="section-title">📚 Házi feladatok</div>
  <div id="haziLog" style="background:#1e293b;color:#94a3b8;border-radius:9px;padding:12px;font-size:12px;font-family:monospace;white-space:pre-wrap;max-height:120px;overflow-y:auto;margin-bottom:12px;display:none"></div>
  <div id="haziList"></div>
</div>

<script>
let profiles = [], editIdx = -1, activeIdx = -1, lastNapok = null, lastSzinek = {};

async function loadProfiles() {
  profiles = await (await fetch('/api/profiles')).json();
  renderProfiles();
}

function renderProfiles() {
  const el = document.getElementById('profileList');
  if (!profiles.length) { el.innerHTML = '<div style="color:#888;font-size:13px;padding:8px 0">Még nincs profil.</div>'; return; }
  el.innerHTML = profiles.map((p,i) => `
    <div class="profile-row ${i===activeIdx?'active':''}" onclick="selectProfile(${i})">
      <div><div class="profile-name">${p.name}</div><div class="profile-sub">${p.school_code}.e-kreta.hu</div></div>
      <button class="btn-secondary" style="flex:none;padding:6px 12px;font-size:12px" onclick="event.stopPropagation();editProfile(${i})">✏️</button>
    </div>`).join('');
}

function selectProfile(i) {
  activeIdx = i; renderProfiles();
  document.getElementById('fetchCard').style.display = 'block';
  document.getElementById('selectedLabel').textContent = profiles[i].name;
  document.getElementById('resultCard').style.display = 'none';
  document.getElementById('log').style.display = 'none';
  document.getElementById('haziBtn').style.display = '';
}

function newProfile() {
  editIdx = -1;
  document.getElementById('editTitle').textContent = 'Új profil';
  ['f_name','f_user','f_pass'].forEach(id => document.getElementById(id).value='');
  document.getElementById('f_school').value = 'szenterzsebet';
  document.getElementById('f_hetek').value = '2';
  document.getElementById('deleteBtn').style.display = 'none';
  document.getElementById('editCard').style.display = 'block';
}

function editProfile(i) {
  editIdx = i; const p = profiles[i];
  document.getElementById('editTitle').textContent = 'Profil szerkesztése';
  document.getElementById('f_name').value = p.name;
  document.getElementById('f_school').value = p.school_code;
  document.getElementById('f_user').value = p.username;
  document.getElementById('f_pass').value = p.password || '';
  document.getElementById('f_hetek').value = p.hetek || 2;
  document.getElementById('deleteBtn').style.display = 'inline-block';
  document.getElementById('editCard').style.display = 'block';
}

function cancelEdit() { document.getElementById('editCard').style.display = 'none'; }

async function saveProfile() {
  const p = {name:document.getElementById('f_name').value.trim(),school_code:document.getElementById('f_school').value.trim(),username:document.getElementById('f_user').value.trim(),password:document.getElementById('f_pass').value,hetek:parseInt(document.getElementById('f_hetek').value)||2};
  if (!p.name||!p.school_code||!p.username){alert('Töltsd ki a kötelező mezőket!');return;}
  await fetch('/api/profiles',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({idx:editIdx,profile:p})});
  document.getElementById('editCard').style.display='none';
  await loadProfiles();
}

async function deleteProfile() {
  if (!confirm('Törlöd?')) return;
  await fetch('/api/profiles/'+editIdx,{method:'DELETE'});
  editIdx=-1; activeIdx=-1;
  document.getElementById('editCard').style.display='none';
  document.getElementById('fetchCard').style.display='none';
  document.getElementById('resultCard').style.display='none';
  document.getElementById('haziCard').style.display='none';
  document.getElementById('haziBtn').style.display='none';
  await loadProfiles();
}

async function doFetch() {
  if (activeIdx<0) return;
  const btn = document.getElementById('fetchBtn');
  btn.innerHTML='<span class="spinner"></span>Letöltés...'; btn.disabled=true;
  const logEl = document.getElementById('log');
  logEl.style.display='block'; logEl.textContent='';
  document.getElementById('resultCard').style.display='none';

  const r = await fetch('/api/fetch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({idx:activeIdx})});
  const data = await r.json();

  logEl.textContent = data.logs.join('\\n');
  if (data.error) { logEl.textContent += '\\nHIBA: '+data.error; }
  else { showResult(data); }

  btn.innerHTML='⬇ Órarend letöltése'; btn.disabled=false;
}

function showResult(data) {
  lastNapok = data.napok;
  lastSzinek = data.szinek || {};
  document.getElementById('resultCard').style.display='block';
  document.getElementById('configOut').style.display='block';
  document.getElementById('configOut').textContent = data.config;
  renderTable(data.napok, lastSzinek);
}

function renderTable(napok, szinek) {
  szinek = szinek || {};
  const napKeys = ['hetfo','kedd','szerda','csutortok','pentek'];
  const napNevek = ['Hétfő','Kedd','Szerda','Csütörtök','Péntek'];
  const hanyadikok = [...new Set(napKeys.flatMap(n => (napok[n]||[]).map(o=>o.hanyadik)))].sort((a,b)=>a-b);
  const grid = {};
  napKeys.forEach(n => (napok[n]||[]).forEach(o => { grid[n+'-'+o.hanyadik] = o; }));

  let html = '<thead><tr><th>#</th>'+napNevek.map(n=>`<th>${n}</th>`).join('')+'</tr></thead><tbody>';
  hanyadikok.forEach(h => {
    html += `<tr><td class="ora-num">${h}.</td>`;
    napKeys.forEach(n => {
      const o = grid[n+'-'+h];
      if (o) {
        const hex = szinek[o.targy] || o.color || '#94a3b8';
        const r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);
        const bg=`rgba(${r},${g},${b},0.12)`;
        html += `<td><div class="ora-cell" style="background:${bg};border-left:3px solid ${hex}">
          <div class="ora-targy" style="color:${hex}">${o.targy}</div>
          <div class="ora-time">⏰ ${o.tol}–${o.ig}</div>
          ${o.tanar?`<div class="ora-tanar">👤 ${o.tanar}</div>`:''}
          ${o.terem?`<div class="ora-terem">🚪 ${o.terem}</div>`:''}
        </div></td>`;
      } else {
        html += '<td class="empty-cell"></td>';
      }
    });
    html += '</tr>';
  });
  html += '</tbody>';
  document.getElementById('ttTable').innerHTML = html;
}

async function downloadExcel() {
  window.location='/api/excel/'+activeIdx;
}

function copyConfig() {
  const text = document.getElementById('configOut').textContent;
  navigator.clipboard.writeText(text).then(()=>alert('Config másolva!'));
}

async function doFetchHazi() {
  if (activeIdx < 0) return;
  const btn = document.getElementById('haziBtn');
  btn.innerHTML = '<span class="spinner"></span>Letöltés...'; btn.disabled = true;
  const logEl = document.getElementById('haziLog');
  logEl.style.display = 'block'; logEl.textContent = '';
  document.getElementById('haziCard').style.display = 'block';
  document.getElementById('haziList').innerHTML = '<div style="color:#888;padding:12px">Betöltés...</div>';

  const r = await fetch('/api/fetch_hazi', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({idx: activeIdx})});
  const data = await r.json();
  logEl.textContent = data.logs.join('\\n');
  if (data.error) { logEl.textContent += '\\nHIBA: ' + data.error; }
  else { renderHaziList(data.hazi_lista); }
  btn.innerHTML = '📚 Házi feladatok letöltése'; btn.disabled = false;
}

function renderHaziList(lista) {
  const el = document.getElementById('haziList');
  if (!lista || !lista.length) {
    el.innerHTML = '<div style="color:#888;padding:12px">Nincs házi feladat.</div>';
    return;
  }
  const allCs = [];
  lista.forEach(hf => (hf._Csatolmanyok||[]).forEach(cs => allCs.push({cs_id: cs.ID, fajlnev: cs.FajlNev, kiterjesztes: cs.FajlKiterjesztes})));

  let html = '';
  if (allCs.length > 0) {
    html += `<div style="margin-bottom:12px"><button class="btn-primary" onclick="downloadAllCsatolmanyok(event)">📥 Összes melléklet letöltése (${allCs.length} fájl)</button></div>`;
  }
  html += '<table style="width:100%;border-collapse:collapse;font-size:13px">';
  html += '<thead><tr style="background:#1a56db;color:#fff"><th style="padding:8px 6px;text-align:left">Tantárgy</th><th style="padding:8px 6px;text-align:left">Feladat</th><th style="padding:8px 6px;text-align:left">Határidő</th><th style="padding:8px 6px;text-align:left">Tanár</th><th style="padding:8px 6px;text-align:left">Mellékletek</th></tr></thead><tbody>';
  lista.forEach((hf, i) => {
    const bg = i % 2 === 0 ? '#f8fafc' : '#fff';
    const hatarido = hf.HaziFeladatHatarido ? hf.HaziFeladatHatarido.slice(0,10) : '–';
    const done = hf.MegoldottHF_BOOL ? '✅ ' : '';
    const csHtml = (hf._Csatolmanyok||[]).map(cs => {
      const mb = cs.FajlMeret ? `(${(cs.FajlMeret/1024/1024).toFixed(1)}MB)` : '';
      const fname = encodeURIComponent(`${cs.FajlNev}.${cs.FajlKiterjesztes}`);
      const url = `/api/download_csatolmany_one/${activeIdx}/${cs.ID}?fname=${fname}`;
      return `<a href="${url}" download style="display:inline-flex;align-items:center;gap:4px;background:#dbeafe;color:#1e40af;padding:3px 8px;border-radius:5px;margin:2px;font-size:11px;font-weight:600;text-decoration:none">📎 ${cs.FajlNev}.${cs.FajlKiterjesztes} ${mb}</a>`;
    }).join('');
    html += `<tr style="background:${bg};border-bottom:1px solid #e0e7ef">
      <td style="padding:8px 6px;font-weight:700;color:#1a56db">${hf.TantargyNev||'–'}</td>
      <td style="padding:8px 6px">${done}${hf.HaziFeladatSzoveg||'–'}</td>
      <td style="padding:8px 6px;color:#374151;white-space:nowrap">${hatarido}</td>
      <td style="padding:8px 6px;font-size:12px;color:#64748b">${hf.TanarNeve||'–'}</td>
      <td style="padding:8px 6px">${csHtml||'–'}</td>
    </tr>`;
  });
  html += '</tbody></table>';
  el.innerHTML = html;
  window._haziCsatolmanyok = allCs;
}

function downloadAllCsatolmanyok(event) {
  if (!window._haziCsatolmanyok || !window._haziCsatolmanyok.length) return;
  const ids = window._haziCsatolmanyok.map(c => c.cs_id).join(',');
  window.location.href = `/api/download_zip/${activeIdx}?ids=${ids}`;
}

loadProfiles();
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/profiles", methods=["GET"])
def get_profiles():
    return jsonify(load_config())

@app.route("/api/profiles", methods=["POST"])
def upsert_profile():
    data = request.get_json()
    profiles = load_config()
    idx = data.get("idx", -1)
    if idx == -1:
        profiles.append(data["profile"])
    else:
        profiles[idx] = data["profile"]
    save_config(profiles)
    return jsonify({"ok": True})

@app.route("/api/profiles/<int:idx>", methods=["DELETE"])
def delete_profile(idx):
    profiles = load_config()
    if 0 <= idx < len(profiles):
        profiles.pop(idx)
        save_config(profiles)
    return jsonify({"ok": True})

@app.route("/api/fetch", methods=["POST"])
def do_fetch():
    data = request.get_json()
    profiles = load_config()
    idx = data.get("idx", 0)
    if idx < 0 or idx >= len(profiles):
        return jsonify({"error": "Érvénytelen profil", "logs": []})
    p = profiles[idx]
    logs = []
    try:
        result = fetch_orarend(p["school_code"], p["username"], p["password"], p.get("hetek", 2), logs)
        # Config fájlba is menti
        out = Path(__file__).parent / "kreta_orarend_output.txt"
        out.write_text(result["config"] + "\n", encoding="utf-8")
        logs.append(f"Mentve: {out.name}")
        return jsonify({"config": result["config"], "napok": result["napok"], "szinek": result["szinek"], "logs": logs})
    except Exception as e:
        logs.append(f"KIVÉTEL: {e}")
        return jsonify({"error": str(e), "logs": logs})

@app.route("/api/excel/<int:idx>")
def download_excel(idx):
    profiles = load_config()
    if idx < 0 or idx >= len(profiles):
        return "Érvénytelen profil", 404
    p = profiles[idx]
    try:
        result = fetch_orarend(p["school_code"], p["username"], p["password"], p.get("hetek", 2))
        xlsx = build_excel(result["napok"], p["name"], result.get("szinek"))
        return send_file(
            io.BytesIO(xlsx),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"orarend_{p['name'].replace(' ','_')}.xlsx",
        )
    except Exception as e:
        return str(e), 500


@app.route("/api/fetch_hazi", methods=["POST"])
def do_fetch_hazi():
    data = request.get_json()
    profiles = load_config()
    idx = data.get("idx", 0)
    if idx < 0 or idx >= len(profiles):
        return jsonify({"error": "Érvénytelen profil", "logs": []})
    p = profiles[idx]
    logs = []
    try:
        result = fetch_hazifeladatok_all(p["school_code"], p["username"], p["password"], logs)
        return jsonify({"hazi_lista": result["hazi_lista"], "logs": logs})
    except Exception as e:
        logs.append(f"KIVÉTEL: {e}")
        return jsonify({"error": str(e), "logs": logs})


@app.route("/api/download_zip/<int:idx>")
def download_zip_get(idx):
    """GET endpoint for ZIP download – iOS Safari compatible (browser navigates to URL)."""
    ids_str = request.args.get("ids", "")
    cs_ids = [int(x) for x in ids_str.split(",") if x.strip().isdigit()]
    profiles = load_config()
    if idx < 0 or idx >= len(profiles) or not cs_ids:
        return "Érvénytelen paraméter", 400
    p = profiles[idx]
    try:
        session = get_cached_session(p["school_code"], p["username"], p["password"])
        base = f"https://{p['school_code']}.e-kreta.hu"
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for cs_id in cs_ids:
                dl_resp = session.post(
                    f"{base}/api/HaziFeladatCsatolmanyokApi/DownloadCsatolmanyFile",
                    data={"Id": cs_id},
                    headers={"Referer": f"{base}/Tanulo/TanuloHaziFeladat"},
                )
                if dl_resp.ok and len(dl_resp.content) > 0:
                    cd = dl_resp.headers.get("Content-Disposition", "")
                    fname = re.search(r'filename="?([^"]+)"?', cd)
                    fname = fname.group(1) if fname else f"csatolmany_{cs_id}"
                    zf.writestr(fname, dl_resp.content)
        buf.seek(0)
        return send_file(
            buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"hazifeladat_mellekeletek_{p['name'].replace(' ','_')}.zip",
        )
    except Exception as e:
        return str(e), 500


@app.route("/api/download_csatolmanyok/<int:idx>", methods=["POST"])
def download_csatolmanyok_zip(idx):
    data = request.get_json()
    items = data.get("items", [])
    profiles = load_config()
    if idx < 0 or idx >= len(profiles):
        return "Érvénytelen profil", 404
    p = profiles[idx]
    try:
        session = get_cached_session(p["school_code"], p["username"], p["password"])
        base = f"https://{p['school_code']}.e-kreta.hu"

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in items:
                cs_id = item["cs_id"]
                fname = f"{item['fajlnev']}.{item['kiterjesztes']}"
                dl_resp = session.post(
                    f"{base}/api/HaziFeladatCsatolmanyokApi/DownloadCsatolmanyFile",
                    data={"Id": cs_id},
                    headers={"Referer": f"{base}/Tanulo/TanuloHaziFeladat"},
                )
                if dl_resp.ok and len(dl_resp.content) > 0:
                    zf.writestr(fname, dl_resp.content)
        buf.seek(0)
        return send_file(
            buf,
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"hazifeladat_mellekeletek_{p['name'].replace(' ','_')}.zip",
        )
    except Exception as e:
        return str(e), 500


@app.route("/api/download_csatolmany_one/<int:idx>/<int:cs_id>")
def download_csatolmany_one(idx, cs_id):
    """Download a single attachment file, streamed through Flask."""
    from flask import Response
    profiles = load_config()
    if idx < 0 or idx >= len(profiles):
        return Response("Érvénytelen profil", status=404)
    p = profiles[idx]
    fname = request.args.get("fname", f"csatolmany_{cs_id}")
    try:
        session = get_cached_session(p["school_code"], p["username"], p["password"])
        base = f"https://{p['school_code']}.e-kreta.hu"

        dl_resp = session.post(
            f"{base}/api/HaziFeladatCsatolmanyokApi/DownloadCsatolmanyFile",
            data={"Id": cs_id},
            headers={"Referer": f"{base}/Tanulo/TanuloHaziFeladat"},
            allow_redirects=True,
            timeout=30,
        )
        app.logger.info(f"Download cs_id={cs_id}: status={dl_resp.status_code} "
                        f"ct={dl_resp.headers.get('Content-Type')} len={len(dl_resp.content)}")

        if not dl_resp.ok:
            return Response(f"Letöltési hiba: {dl_resp.status_code}\n{dl_resp.text[:300]}",
                            status=502, content_type="text/plain; charset=utf-8")

        ct = dl_resp.headers.get("Content-Type", "application/octet-stream")
        cd = dl_resp.headers.get("Content-Disposition") or f'attachment; filename="{fname}"'
        return Response(dl_resp.content, content_type=ct,
                        headers={"Content-Disposition": cd})
    except Exception as e:
        app.logger.error(f"Download exception cs_id={cs_id}: {e}")
        return Response(str(e), status=500, content_type="text/plain; charset=utf-8")


if __name__ == "__main__":
    threading.Timer(1.2, lambda: webbrowser.open("http://localhost:5555")).start()
    app.run(port=5555, debug=False)
