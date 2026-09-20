// Google Apps Script – Házi Feladat App v5.1
// CORS enabled
const VERSION = '5.1';

function getSheet(ss, name) { return ss.getSheetByName(name); }

function ensureSheet(ss, name, headers) {
  let sh = ss.getSheetByName(name);
  if (!sh) { sh = ss.insertSheet(name); if (headers) sh.appendRow(headers); }
  return sh;
}

function getConfig(ss) {
  const cfg = ensureSheet(ss, 'Config', ['kulcs','ertek']);
  const vals = cfg.getDataRange().getValues();
  const map = {};
  vals.forEach(r => { if(r[0]) map[String(r[0])] = String(r[1]); });
  return map;
}

function getActiveTanev(ss) {
  return getConfig(ss)['aktiv_tanev'] || '2026-2027';
}

function getSubjectsForTanev(ss, tanev) {
  const cfg = getConfig(ss);
  const key = 'tantargyak_' + tanev;
  return cfg[key] ? cfg[key].split(',').map(s=>s.trim()) : [];
}

function getAllTanevek(ss) {
  const cfg = getConfig(ss);
  const tanevStr = cfg['tanevek'] || getActiveTanev(ss);
  return tanevStr.split(',').map(s=>s.trim()).filter(Boolean);
}

function getFeladatokSheet(ss, tanev) {
  return ensureSheet(ss, 'Feladatok_' + tanev, [
    'id','subject','desc','due','note','uploader','uploaded',
    'images','cloudFolder','ocrText','modifiedBy','modifiedAt','type'
  ]);
}

function getKuka(ss) {
  return ensureSheet(ss, 'Kuka', [
    'id','subject','desc','due','note','uploader','uploaded',
    'images','cloudFolder','ocrText','modifiedBy','modifiedAt','type',
    'deletedAt','deletedBy','tanev'
  ]);
}

function getVeglegesTorolve(ss) {
  return ensureSheet(ss, 'Veglegesen_Torolve', [
    'id','subject','desc','due','note','uploader','uploaded',
    'images','cloudFolder','ocrText','modifiedBy','modifiedAt','type',
    'deletedAt','deletedBy','permDeletedAt','permDeletedBy','tanev'
  ]);
}

function getFavs(ss) {
  return ensureSheet(ss, 'Kedvencek', ['userName','hwId','addedAt']);
}

function sanitize(row) {
  return row.map(v => v === null || v === undefined ? '' : String(v));
}

function sheetToRows(sh, fields) {
  const vals = sh.getDataRange().getValues();
  return vals.slice(1).map(r => {
    const obj = {};
    fields.forEach((f,i) => obj[f] = String(r[i]||''));
    return obj;
  }).filter(r => r.id && r.id !== 'id');
}

const HW_FIELDS = ['id','subject','desc','due','note','uploader','uploaded','images','cloudFolder','ocrText','modifiedBy','modifiedAt','type'];
const KUKA_FIELDS = ['id','subject','desc','due','note','uploader','uploaded','images','cloudFolder','ocrText','modifiedBy','modifiedAt','type','deletedAt','deletedBy','tanev'];

function makeResponse(result, cb) {
  const json = JSON.stringify(result);
  if (cb) {
    return ContentService.createTextOutput(cb+'('+json+')')
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  // Return JSON with CORS headers via HTML service trick
  const html = HtmlService.createHtmlOutput(json);
  return ContentService.createTextOutput(json)
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  try {
    const p = e.parameter;
    const sheetId = p.sheetId;
    const action = p.action || 'ping';
    const cb = p.callback;
    let result;

    if (action === 'ping') {
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'loadConfig' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const tanev = getActiveTanev(ss);
      const tanevek = getAllTanevek(ss);
      const subjects = getSubjectsForTanev(ss, tanev);
      result = {status:'ok', version:VERSION, activeTanev:tanev, tanevek, subjects};
    }
    else if (action === 'loadHomeworks' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const tanev = p.tanev || getActiveTanev(ss);
      const sh = getFeladatokSheet(ss, tanev);
      result = {status:'ok', version:VERSION, data:sheetToRows(sh, HW_FIELDS), tanev};
    }
    else if (action === 'loadTrash' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      result = {status:'ok', version:VERSION, data:sheetToRows(getKuka(ss), KUKA_FIELDS)};
    }
    else if (action === 'loadFavs' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const sh = getFavs(ss);
      const vals = sh.getDataRange().getValues();
      const userName = p.userName || '';
      const rows = vals.slice(1)
        .filter(r => String(r[0]) === userName)
        .map(r => String(r[1]))
        .filter(id => id && id !== 'hwId');
      result = {status:'ok', version:VERSION, data:rows};
    }
    else if (action === 'addFav' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const sh = getFavs(ss);
      const userName = p.userName || '', hwId = p.hwId || '';
      const vals = sh.getDataRange().getValues();
      if (!vals.slice(1).some(r => String(r[0])===userName && String(r[1])===hwId))
        sh.appendRow([userName, hwId, new Date().toISOString()]);
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'removeFav' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const sh = getFavs(ss);
      const userName = p.userName || '', hwId = p.hwId || '';
      const vals = sh.getRange('A:B').getValues();
      for (let i = vals.length-1; i >= 1; i--)
        if (String(vals[i][0])===userName && String(vals[i][1])===hwId) { sh.deleteRow(i+1); break; }
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'removeFavHw' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const sh = getFavs(ss);
      const hwId = p.hwId || '';
      const vals = sh.getRange('A:B').getValues();
      for (let i = vals.length-1; i >= 1; i--)
        if (String(vals[i][1])===hwId) sh.deleteRow(i+1);
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'append' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const tanev = p.tanev || getActiveTanev(ss);
      const sh = getFeladatokSheet(ss, tanev);
      sh.appendRow(sanitize(JSON.parse(p.row)));
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'update' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const tanev = p.tanev || getActiveTanev(ss);
      const sh = getFeladatokSheet(ss, tanev);
      const row = sanitize(JSON.parse(p.row));
      const vals = sh.getRange('A:A').getValues();
      for (let i = 0; i < vals.length; i++) {
        if (String(vals[i][0]) === String(p.id)) {
          sh.getRange(i+1,1,1,row.length).setValues([row]);
          result = {status:'ok', version:VERSION}; break;
        }
      }
      if (!result) result = {status:'ok', msg:'not found', version:VERSION};
    }
    else if (action === 'delete' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const tanev = p.tanev || getActiveTanev(ss);
      const sh = getFeladatokSheet(ss, tanev);
      const kuka = getKuka(ss);
      const vals = sh.getRange('A:A').getValues();
      for (let i = 0; i < vals.length; i++) {
        if (String(vals[i][0]) === String(p.id)) {
          const row = sh.getRange(i+1,1,1,Math.max(sh.getLastColumn(),13)).getValues()[0];
          kuka.appendRow(sanitize([
            row[0],row[1],row[2],row[3],row[4],row[5],row[6],
            row[7],row[8]||'',row[9]||'',row[10]||'',row[11]||'',row[12]||'',
            new Date().toISOString(), p.deletedBy||'', tanev
          ]));
          sh.deleteRow(i+1);
          result = {status:'ok', version:VERSION}; break;
        }
      }
      if (!result) result = {status:'ok', msg:'not found', version:VERSION};
    }
    else if (action === 'restore' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const kuka = getKuka(ss);
      const vals = kuka.getRange('A:A').getValues();
      for (let i = 1; i < vals.length; i++) {
        if (String(vals[i][0]) === String(p.id)) {
          const row = kuka.getRange(i+1,1,1,16).getValues()[0];
          const tanev = String(row[15]) || getActiveTanev(ss);
          const sh = getFeladatokSheet(ss, tanev);
          const newId = String(Date.now());
          sh.appendRow(sanitize([newId,row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8]||'',row[9]||'',row[10]||'',row[11]||'',row[12]||'']));
          kuka.deleteRow(i+1);
          result = {status:'ok', newId, version:VERSION}; break;
        }
      }
      if (!result) result = {status:'ok', msg:'not found', version:VERSION};
    }
    else if (action === 'permDelete' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const kuka = getKuka(ss);
      const perm = getVeglegesTorolve(ss);
      const vals = kuka.getRange('A:A').getValues();
      for (let i = vals.length-1; i >= 1; i--) {
        if (String(vals[i][0]) === String(p.id)) {
          const row = kuka.getRange(i+1,1,1,16).getValues()[0];
          perm.appendRow(sanitize([
            row[0],row[1],row[2],row[3],row[4],row[5],row[6],
            row[7],row[8]||'',row[9]||'',row[10]||'',row[11]||'',row[12]||'',
            row[13]||'',row[14]||'',
            new Date().toISOString(), p.deletedBy||'', row[15]||''
          ]));
          kuka.deleteRow(i+1);
          result = {status:'ok', version:VERSION}; break;
        }
      }
      if (!result) result = {status:'ok', msg:'not found', version:VERSION};
    }
    else {
      result = {status:'unknown', action, version:VERSION};
    }

    return makeResponse(result, cb);

  } catch(err) {
    const out = {status:'error', message:err.toString(), version:VERSION};
    return makeResponse(out, e.parameter.callback);
  }
}

function doPost(e) {
  return makeResponse({status:'ok', msg:'use GET', version:VERSION}, null);
}
