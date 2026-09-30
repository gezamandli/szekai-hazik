#!/usr/bin/env python3.11
"""
Kréta órarend letöltő – webes felület + Excel export
Telepítés: pip3.11 install flask beautifulsoup4 requests openpyxl
Futtatás:  ./kreta_orarend.py
"""

import io
import json
import threading
import webbrowser
from datetime import date, timedelta, datetime
from pathlib import Path
from time import sleep

import requests
from bs4 import BeautifulSoup as bs
from flask import Flask, jsonify, render_template_string, request, send_file

CONFIG_FILE = Path(__file__).parent / "kreta_config.json"

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


if __name__ == "__main__":
    threading.Timer(1.2, lambda: webbrowser.open("http://localhost:5555")).start()
    app.run(port=5555, debug=False)
