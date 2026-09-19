// Google Apps Script – Házi Feladat App v2
// Deploy: Execute as Me, Anyone can access

const VERSION = '2.1';

function getSheets(sheetId) {
  const ss = SpreadsheetApp.openById(sheetId);
  let main = ss.getSheetByName('Feladatok') || ss.getSheets()[0];
  if (main.getName() !== 'Feladatok') main.setName('Feladatok');
  let trash = ss.getSheetByName('Kuka');
  if (!trash) {
    trash = ss.insertSheet('Kuka');
    trash.appendRow(['id','subject','desc','due','note','uploader','uploaded','images','cloudFolder','deletedAt','deletedBy']);
  }
  return { ss, main, trash };
}

function doGet(e) {
  try {
    const p = e.parameter;
    const sheetId = p.sheetId;
    const action  = p.action || 'ping';

    if (action === 'ping') {
      return json({status:'ok', version: VERSION});
    }

    if (action === 'loadTrash') {
      const { trash } = getSheets(sheetId);
      const vals = trash.getDataRange().getValues();
      const rows = vals.slice(1).map(r => ({
        id: String(r[0]), subject: String(r[1]), desc: String(r[2]),
        due: String(r[3]), note: String(r[4]), uploader: String(r[5]),
        uploaded: String(r[6]), images: String(r[7]), cloudFolder: String(r[8]),
        deletedAt: String(r[9]), deletedBy: String(r[10])
      })).filter(r => r.id && r.id !== 'id');
      return json({status:'ok', version: VERSION, data: rows});
    }

    if (action === 'append') {
      const { main } = getSheets(sheetId);
      const row = JSON.parse(p.row);
      main.appendRow(row);
      return json({status:'ok', version: VERSION});
    }

    if (action === 'update') {
      const { main } = getSheets(sheetId);
      const row = JSON.parse(p.row);
      const id  = p.id;
      const vals = main.getRange('A:A').getValues();
      for (let i = 0; i < vals.length; i++) {
        if (String(vals[i][0]) === String(id)) {
          main.getRange(i+1, 1, 1, row.length).setValues([row]);
          return json({status:'ok', version: VERSION});
        }
      }
      return json({status:'ok', msg:'not found', version: VERSION});
    }

    if (action === 'delete') {
      const { main, trash } = getSheets(sheetId);
      const id = p.id;
      const deletedBy = p.deletedBy || '';
      const vals = main.getRange('A:A').getValues();
      for (let i = 0; i < vals.length; i++) {
        if (String(vals[i][0]) === String(id)) {
          const lastCol = main.getLastColumn();
          const row = main.getRange(i+1, 1, 1, Math.max(lastCol,9)).getValues()[0];
          const trashRow = [
            row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8]||'',
            new Date().toISOString(), deletedBy
          ];
          trash.appendRow(trashRow);
          main.deleteRow(i + 1);
          return json({status:'ok', version: VERSION});
        }
      }
      return json({status:'ok', msg:'not found', version: VERSION});
    }

    if (action === 'restore') {
      const { main, trash } = getSheets(sheetId);
      const id = p.id;
      const vals = trash.getRange('A:A').getValues();
      for (let i = 1; i < vals.length; i++) {
        if (String(vals[i][0]) === String(id)) {
          const row = trash.getRange(i+1, 1, 1, 9).getValues()[0];
          const newId = String(Date.now());
          row[0] = newId;
          main.appendRow(row);
          trash.deleteRow(i + 1);
          return json({status:'ok', newId: newId, version: VERSION});
        }
      }
      return json({status:'ok', msg:'not found', version: VERSION});
    }

    if (action === 'permDelete') {
      const { trash } = getSheets(sheetId);
      const id = p.id;
      const vals = trash.getRange('A:A').getValues();
      for (let i = 1; i < vals.length; i++) {
        if (String(vals[i][0]) === String(id)) {
          trash.deleteRow(i + 1);
          return json({status:'ok', version: VERSION});
        }
      }
      return json({status:'ok', msg:'not found', version: VERSION});
    }

    return json({status:'unknown', action, version: VERSION});

  } catch(err) {
    return json({status:'error', message: err.toString(), version: VERSION});
  }
}

function doPost(e) {
  // Fallback – minden GET-tel megy, POST nem szükséges
  return json({status:'ok', msg:'use GET', version: VERSION});
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
