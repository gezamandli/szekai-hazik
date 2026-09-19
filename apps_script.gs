// Google Apps Script – Házi Feladat App v4.1
// CORS-enabled via HtmlService trick
const VERSION = '4.1';

function getSheets(sheetId) {
  const ss = SpreadsheetApp.openById(sheetId);
  let main = ss.getSheetByName('Feladatok') || ss.getSheets()[0];
  if (main.getName() !== 'Feladatok') main.setName('Feladatok');
  let trash = ss.getSheetByName('Kuka');
  if (!trash) {
    trash = ss.insertSheet('Kuka');
    trash.appendRow(['id','subject','desc','due','note','uploader','uploaded','images','cloudFolder','deletedAt','deletedBy']);
  }
  let favs = ss.getSheetByName('Kedvencek');
  if (!favs) {
    favs = ss.insertSheet('Kedvencek');
    favs.appendRow(['userName','hwId','addedAt']);
  }
  return { ss, main, trash, favs };
}

function sanitizeRow(row) {
  return row.map(val => val === null || val === undefined ? '' : String(val));
}

function corsResponse(data) {
  const output = ContentService.createTextOutput(JSON.stringify(data));
  output.setMimeType(ContentService.MimeType.JSON);
  return output;
}

function doGet(e) {
  try {
    const p = e.parameter;
    const sheetId = p.sheetId;
    const action  = p.action || 'ping';

    let result;

    if (action === 'ping') {
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'loadTrash' && sheetId) {
      const { trash } = getSheets(sheetId);
      const vals = trash.getDataRange().getValues();
      const rows = vals.slice(1).map(r => ({
        id:String(r[0]), subject:String(r[1]), desc:String(r[2]),
        due:String(r[3]), note:String(r[4]), uploader:String(r[5]),
        uploaded:String(r[6]), images:String(r[7]), cloudFolder:String(r[8]),
        deletedAt:String(r[9]), deletedBy:String(r[10])
      })).filter(r => r.id && r.id !== 'id');
      result = {status:'ok', version:VERSION, data:rows};
    }
    else if (action === 'loadFavs' && sheetId) {
      const { favs } = getSheets(sheetId);
      const vals = favs.getDataRange().getValues();
      const userName = p.userName || '';
      const rows = vals.slice(1)
        .filter(r => String(r[0]) === userName)
        .map(r => String(r[1]))
        .filter(id => id && id !== 'hwId');
      result = {status:'ok', version:VERSION, data:rows};
    }
    else if (action === 'addFav' && sheetId) {
      const { favs } = getSheets(sheetId);
      const userName = p.userName || '';
      const hwId = p.hwId || '';
      const vals = favs.getDataRange().getValues();
      const exists = vals.slice(1).some(r => String(r[0])===userName && String(r[1])===hwId);
      if (!exists) favs.appendRow([userName, hwId, new Date().toISOString()]);
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'removeFav' && sheetId) {
      const { favs } = getSheets(sheetId);
      const userName = p.userName || '';
      const hwId = p.hwId || '';
      const vals = favs.getRange('A:B').getValues();
      for (let i = vals.length-1; i >= 1; i--) {
        if (String(vals[i][0])===userName && String(vals[i][1])===hwId) {
          favs.deleteRow(i+1); break;
        }
      }
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'removeFavHw' && sheetId) {
      const { favs } = getSheets(sheetId);
      const hwId = p.hwId || '';
      const vals = favs.getRange('A:B').getValues();
      for (let i = vals.length-1; i >= 1; i--) {
        if (String(vals[i][1])===hwId) favs.deleteRow(i+1);
      }
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'append' && sheetId) {
      const { main } = getSheets(sheetId);
      const row = JSON.parse(p.row);
      main.appendRow(sanitizeRow(row));
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'update' && sheetId) {
      const { main } = getSheets(sheetId);
      const row = JSON.parse(p.row);
      const vals = main.getRange('A:A').getValues();
      for (let i = 0; i < vals.length; i++) {
        if (String(vals[i][0]) === String(p.id)) {
          main.getRange(i+1,1,1,sanitizeRow(row).length).setValues([sanitizeRow(row)]);
          result = {status:'ok', version:VERSION}; break;
        }
      }
      if (!result) result = {status:'ok', msg:'not found', version:VERSION};
    }
    else if (action === 'delete' && sheetId) {
      const { main, trash } = getSheets(sheetId);
      const vals = main.getRange('A:A').getValues();
      for (let i = 0; i < vals.length; i++) {
        if (String(vals[i][0]) === String(p.id)) {
          const lastCol = Math.max(main.getLastColumn(), 9);
          const row = main.getRange(i+1,1,1,lastCol).getValues()[0];
          trash.appendRow([String(row[0]),String(row[1]),String(row[2]),String(row[3]),
            String(row[4]),String(row[5]),String(row[6]),String(row[7]),
            String(row[8]||''), new Date().toISOString(), String(p.deletedBy||'')]);
          main.deleteRow(i+1);
          result = {status:'ok', version:VERSION}; break;
        }
      }
      if (!result) result = {status:'ok', msg:'not found', version:VERSION};
    }
    else if (action === 'restore' && sheetId) {
      const { main, trash } = getSheets(sheetId);
      const vals = trash.getRange('A:A').getValues();
      for (let i = 1; i < vals.length; i++) {
        if (String(vals[i][0]) === String(p.id)) {
          const row = trash.getRange(i+1,1,1,9).getValues()[0];
          row[0] = String(Date.now());
          main.appendRow(sanitizeRow(row));
          trash.deleteRow(i+1);
          result = {status:'ok', newId:row[0], version:VERSION}; break;
        }
      }
      if (!result) result = {status:'ok', msg:'not found', version:VERSION};
    }
    else if (action === 'permDelete' && sheetId) {
      const { trash } = getSheets(sheetId);
      const vals = trash.getRange('A:A').getValues();
      for (let i = vals.length-1; i >= 1; i--) {
        if (String(vals[i][0]) === String(p.id)) {
          trash.deleteRow(i+1); break;
        }
      }
      result = {status:'ok', version:VERSION};
    }
    else {
      result = {status:'unknown', action, version:VERSION};
    }

    // Return with JSONP if callback provided, else plain JSON
    const jsonStr = JSON.stringify(result);
    const cb = p.callback;
    if (cb) {
      return ContentService.createTextOutput(cb+'('+jsonStr+')')
        .setMimeType(ContentService.MimeType.JAVASCRIPT);
    }
    return ContentService.createTextOutput(jsonStr)
      .setMimeType(ContentService.MimeType.JSON);

  } catch(err) {
    const out = JSON.stringify({status:'error', message:err.toString(), version:VERSION});
    const cb = e.parameter.callback;
    if (cb) return ContentService.createTextOutput(cb+'('+out+')').setMimeType(ContentService.MimeType.JAVASCRIPT);
    return ContentService.createTextOutput(out).setMimeType(ContentService.MimeType.JSON);
  }
}

function doPost(e) {
  return ContentService.createTextOutput(JSON.stringify({status:'ok',msg:'use GET',version:VERSION}))
    .setMimeType(ContentService.MimeType.JSON);
}
