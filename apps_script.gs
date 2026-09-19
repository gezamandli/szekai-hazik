// Google Apps Script – Házi Feladat App backend
// Deploy as Web App: Execute as Me, Anyone can access
// FONTOS: Content-Type legyen text/plain a POST kéréseknél

function getOrCreateSheets(sheetId) {
  const ss = SpreadsheetApp.openById(sheetId);
  let main = ss.getSheetByName('Feladatok');
  if (!main) {
    main = ss.getSheets()[0];
    main.setName('Feladatok');
  }
  let trash = ss.getSheetByName('Kuka');
  if (!trash) {
    trash = ss.insertSheet('Kuka');
    trash.appendRow(['id','subject','desc','due','note','uploader','uploaded','images','cloudFolder','deletedAt','deletedBy']);
  }
  return { ss, main, trash };
}

function doGet(e) {
  const params = e.parameter;
  const sheetId = params.sheetId;
  const action = params.action;

  if (action === 'loadTrash' && sheetId) {
    try {
      const { trash } = getOrCreateSheets(sheetId);
      const vals = trash.getDataRange().getValues();
      const rows = vals.slice(1).map(r => ({
        id: String(r[0]), subject: r[1], desc: r[2], due: r[3],
        note: r[4], uploader: r[5], uploaded: r[6],
        images: r[7], cloudFolder: r[8],
        deletedAt: r[9], deletedBy: r[10]
      })).filter(r => r.id);
      return ContentService
        .createTextOutput(JSON.stringify({status:'ok', data: rows}))
        .setMimeType(ContentService.MimeType.JSON);
    } catch(err) {
      return ContentService
        .createTextOutput(JSON.stringify({status:'error', message: err.toString()}))
        .setMimeType(ContentService.MimeType.JSON);
    }
  }

  return ContentService
    .createTextOutput(JSON.stringify({status:'ok'}))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const sheetId = data.sheetId;
    const { main, trash } = getOrCreateSheets(sheetId);

    if (data.action === 'append') {
      main.appendRow(data.row);
      return ok();
    }

    if (data.action === 'update') {
      const vals = main.getRange('A:A').getValues();
      for (let i = 0; i < vals.length; i++) {
        if (String(vals[i][0]) === String(data.id)) {
          main.getRange(i+1, 1, 1, data.row.length).setValues([data.row]);
          return ok();
        }
      }
      return ok('not found');
    }

    if (data.action === 'delete') {
      const vals = main.getRange('A:A').getValues();
      for (let i = 0; i < vals.length; i++) {
        if (String(vals[i][0]) === String(data.id)) {
          const row = main.getRange(i+1, 1, 1, 9).getValues()[0];
          row.push(new Date().toISOString());
          row.push(data.deletedBy || '');
          trash.appendRow(row);
          main.deleteRow(i + 1);
          return ok();
        }
      }
      return ok('not found');
    }

    if (data.action === 'restore') {
      const vals = trash.getRange('A:A').getValues();
      for (let i = 1; i < vals.length; i++) {
        if (String(vals[i][0]) === String(data.id)) {
          const row = trash.getRange(i+1, 1, 1, 9).getValues()[0];
          row[0] = String(Date.now());
          main.appendRow(row);
          trash.deleteRow(i + 1);
          return ContentService
            .createTextOutput(JSON.stringify({status:'ok', newId: row[0]}))
            .setMimeType(ContentService.MimeType.JSON);
        }
      }
      return ok('not found');
    }

    if (data.action === 'permDelete') {
      const vals = trash.getRange('A:A').getValues();
      for (let i = 1; i < vals.length; i++) {
        if (String(vals[i][0]) === String(data.id)) {
          trash.deleteRow(i + 1);
          return ok();
        }
      }
      return ok('not found');
    }

    return ok('unknown action');

  } catch(err) {
    return ContentService
      .createTextOutput(JSON.stringify({status:'error', message: err.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function ok(msg) {
  return ContentService
    .createTextOutput(JSON.stringify({status:'ok', msg: msg||''}))
    .setMimeType(ContentService.MimeType.JSON);
}
