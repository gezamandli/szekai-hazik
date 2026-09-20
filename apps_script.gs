// Google Apps Script – Házi Feladat App v5.2
const VERSION = '5.2';

function ensureSheet(ss, name, headers) {
  try {
    let sh = ss.getSheetByName(name);
    if (!sh) {
      sh = ss.insertSheet(name);
      if (headers) sh.appendRow(headers);
    } else if (headers && sh.getLastRow() === 0) {
      sh.appendRow(headers);
    }
    return sh;
  } catch(e) {
    // Sheet might already exist if concurrent request
    let sh = ss.getSheetByName(name);
    if (sh) return sh;
    throw e;
  }
}

function getConfig(ss) {
  const cfg = ensureSheet(ss, 'Config', ['kulcs','ertek']);
  const vals = cfg.getDataRange().getValues();
  const map = {};
  vals.forEach(r => { if(r[0]) map[String(r[0])] = String(r[1]); });
  return map;
}

function getActiveTanev(ss) { return getConfig(ss)['aktiv_tanev'] || '2026-2027'; }

function getAllTanevek(ss) {
  const cfg = getConfig(ss);
  return (cfg['tanevek']||getActiveTanev(ss)).split(',').map(s=>s.trim()).filter(Boolean);
}

function getSubjectsForTanev(ss, tanev) {
  const cfg = getConfig(ss);
  return (cfg['tantargyak_'+tanev]||'').split(',').map(s=>s.trim()).filter(Boolean);
}

function getFeladatokSheet(ss, tanev) {
  return ensureSheet(ss, 'Feladatok_'+tanev, [
    'id','subject','desc','due','note','uploader','uploaded',
    'images','cloudFolder','ocrText','modifiedBy','modifiedAt','type'
  ]);
}

function getDocsSheet(ss, tanev) {
  return ensureSheet(ss, 'Dokumentumok_'+tanev, [
    'id','title','desc','tags','uploader','uploaded','files','cloudFolder','modifiedBy','modifiedAt'
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

function getFavs(ss) { return ensureSheet(ss, 'Kedvencek', ['userName','hwId','addedAt']); }
function getDocFavs(ss) { return ensureSheet(ss, 'DokumentumKedvencek', ['userName','docId','addedAt']); }

function sanitize(row) { return row.map(v => v==null?'':String(v)); }

function sheetToRows(sh, fields) {
  const vals = sh.getDataRange().getValues();
  return vals.slice(1).map(r => {
    const obj = {};
    fields.forEach((f,i) => obj[f] = String(r[i]||''));
    return obj;
  }).filter(r => r[fields[0]] && r[fields[0]] !== fields[0]);
}

function makeResponse(result, cb) {
  const json = JSON.stringify(result);
  if (cb) return ContentService.createTextOutput(cb+'('+json+')').setMimeType(ContentService.MimeType.JAVASCRIPT);
  return ContentService.createTextOutput(json).setMimeType(ContentService.MimeType.JSON);
}

const HW_FIELDS = ['id','subject','desc','due','note','uploader','uploaded','images','cloudFolder','ocrText','modifiedBy','modifiedAt','type'];
const KUKA_FIELDS = ['id','subject','desc','due','note','uploader','uploaded','images','cloudFolder','ocrText','modifiedBy','modifiedAt','type','deletedAt','deletedBy','tanev'];
const DOC_FIELDS = ['id','title','desc','tags','uploader','uploaded','files','cloudFolder','modifiedBy','modifiedAt'];

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
      result = {status:'ok', version:VERSION,
        activeTanev:getActiveTanev(ss),
        tanevek:getAllTanevek(ss),
        subjects:getSubjectsForTanev(ss, getActiveTanev(ss))
      };
    }
    else if (action === 'loadHomeworks' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const tanev = p.tanev || getActiveTanev(ss);
      result = {status:'ok', version:VERSION, data:sheetToRows(getFeladatokSheet(ss,tanev), HW_FIELDS), tanev};
    }
    else if (action === 'loadTrash' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      result = {status:'ok', version:VERSION, data:sheetToRows(getKuka(ss), KUKA_FIELDS)};
    }
    else if (action === 'loadFavs' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const vals = getFavs(ss).getDataRange().getValues();
      const userName = p.userName||'';
      result = {status:'ok', version:VERSION, data:vals.slice(1).filter(r=>String(r[0])===userName).map(r=>String(r[1])).filter(Boolean)};
    }
    else if (action === 'loadDocFavs' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const vals = getDocFavs(ss).getDataRange().getValues();
      const userName = p.userName||'';
      result = {status:'ok', version:VERSION, data:vals.slice(1).filter(r=>String(r[0])===userName).map(r=>String(r[1])).filter(Boolean)};
    }
    else if (action === 'addFav' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const sh = getFavs(ss); const userName=p.userName||'', hwId=p.hwId||'';
      const vals = sh.getDataRange().getValues();
      if (!vals.slice(1).some(r=>String(r[0])===userName&&String(r[1])===hwId)) sh.appendRow([userName,hwId,new Date().toISOString()]);
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'removeFav' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const sh = getFavs(ss); const userName=p.userName||'', hwId=p.hwId||'';
      const vals = sh.getRange('A:B').getValues();
      for (let i=vals.length-1;i>=1;i--) if (String(vals[i][0])===userName&&String(vals[i][1])===hwId){sh.deleteRow(i+1);break;}
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'removeFavHw' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const sh = getFavs(ss); const hwId=p.hwId||'';
      const vals = sh.getRange('A:B').getValues();
      for (let i=vals.length-1;i>=1;i--) if (String(vals[i][1])===hwId) sh.deleteRow(i+1);
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'addDocFav' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const sh = getDocFavs(ss); const userName=p.userName||'', docId=p.docId||'';
      const vals = sh.getDataRange().getValues();
      if (!vals.slice(1).some(r=>String(r[0])===userName&&String(r[1])===docId)) sh.appendRow([userName,docId,new Date().toISOString()]);
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'removeDocFav' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const sh = getDocFavs(ss); const userName=p.userName||'', docId=p.docId||'';
      const vals = sh.getRange('A:B').getValues();
      for (let i=vals.length-1;i>=1;i--) if (String(vals[i][0])===userName&&String(vals[i][1])===docId){sh.deleteRow(i+1);break;}
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'append' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const tanev = p.tanev||getActiveTanev(ss);
      getFeladatokSheet(ss,tanev).appendRow(sanitize(JSON.parse(p.row)));
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'appendDoc' && sheetId) {
      console.log('appendDoc start, sheetId='+sheetId+' tanev='+p.tanev);
      const ss = SpreadsheetApp.openById(sheetId);
      console.log('ss opened');
      const tanev = p.tanev || '2026-2027';
      const shName = 'Dokumentumok_' + tanev;
      console.log('looking for sheet: '+shName);
      let sh = ss.getSheetByName(shName);
      if (!sh) {
        console.log('creating sheet');
        sh = ss.insertSheet(shName);
        sh.appendRow(['id','title','desc','tags','uploader','uploaded','files','cloudFolder','modifiedBy','modifiedAt']);
      }
      console.log('appending row');
      const row = JSON.parse(p.row);
      sh.appendRow(sanitize(row));
      console.log('done');
      result = {status:'ok', version:VERSION};
    }
    else if (action === 'update' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const sh = getFeladatokSheet(ss, p.tanev||getActiveTanev(ss));
      const row = sanitize(JSON.parse(p.row));
      const vals = sh.getRange('A:A').getValues();
      for (let i=0;i<vals.length;i++) {
        if (String(vals[i][0])===String(p.id)){sh.getRange(i+1,1,1,row.length).setValues([row]);result={status:'ok',version:VERSION};break;}
      }
      if (!result) result = {status:'ok',msg:'not found',version:VERSION};
    }
    else if (action === 'updateDoc' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const sh = getDocsSheet(ss, p.tanev||getActiveTanev(ss));
      const row = sanitize(JSON.parse(p.row));
      const vals = sh.getRange('A:A').getValues();
      for (let i=0;i<vals.length;i++) {
        if (String(vals[i][0])===String(p.id)){sh.getRange(i+1,1,1,row.length).setValues([row]);result={status:'ok',version:VERSION};break;}
      }
      if (!result) result = {status:'ok',msg:'not found',version:VERSION};
    }
    else if (action === 'delete' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const tanev = p.tanev||getActiveTanev(ss);
      const sh = getFeladatokSheet(ss,tanev);
      const kuka = getKuka(ss);
      const vals = sh.getRange('A:A').getValues();
      for (let i=0;i<vals.length;i++) {
        if (String(vals[i][0])===String(p.id)){
          const row = sh.getRange(i+1,1,1,Math.max(sh.getLastColumn(),13)).getValues()[0];
          kuka.appendRow(sanitize([row[0],row[1],row[2],row[3],row[4],row[5],row[6],
            row[7],row[8]||'',row[9]||'',row[10]||'',row[11]||'',row[12]||'',
            new Date().toISOString(),p.deletedBy||'',tanev]));
          sh.deleteRow(i+1);
          result={status:'ok',version:VERSION};break;
        }
      }
      if (!result) result={status:'ok',msg:'not found',version:VERSION};
    }
    else if (action === 'deleteDoc' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const tanev = p.tanev||getActiveTanev(ss);
      const sh = getDocsSheet(ss, tanev);
      const kuka = ensureSheet(ss, 'Dokumentumok_Kuka', ['id','title','desc','tags','uploader','uploaded','files','cloudFolder','modifiedBy','modifiedAt','deletedAt','deletedBy','tanev']);
      const vals = sh.getRange('A:A').getValues();
      for (let i=vals.length-1;i>=1;i--) {
        if (String(vals[i][0])===String(p.id)){
          const row = sh.getRange(i+1,1,1,10).getValues()[0];
          kuka.appendRow(sanitize([...row, new Date().toISOString(), p.deletedBy||'', tanev]));
          sh.deleteRow(i+1);
          result={status:'ok',version:VERSION};break;
        }
      }
      if (!result) result={status:'ok',msg:'not found',version:VERSION};
    }
    else if (action === 'restore' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const kuka = getKuka(ss);
      const vals = kuka.getRange('A:A').getValues();
      for (let i=1;i<vals.length;i++) {
        if (String(vals[i][0])===String(p.id)){
          const row = kuka.getRange(i+1,1,1,16).getValues()[0];
          const tanev = String(row[15])||getActiveTanev(ss);
          const sh = getFeladatokSheet(ss,tanev);
          const newId = String(Date.now());
          sh.appendRow(sanitize([newId,row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8]||'',row[9]||'',row[10]||'',row[11]||'',row[12]||'']));
          kuka.deleteRow(i+1);
          result={status:'ok',newId,version:VERSION};break;
        }
      }
      if (!result) result={status:'ok',msg:'not found',version:VERSION};
    }
    else if (action === 'permDelete' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const kuka = getKuka(ss);
      const perm = getVeglegesTorolve(ss);
      const vals = kuka.getRange('A:A').getValues();
      for (let i=vals.length-1;i>=1;i--) {
        if (String(vals[i][0])===String(p.id)){
          const row = kuka.getRange(i+1,1,1,16).getValues()[0];
          perm.appendRow(sanitize([row[0],row[1],row[2],row[3],row[4],row[5],row[6],
            row[7],row[8]||'',row[9]||'',row[10]||'',row[11]||'',row[12]||'',
            row[13]||'',row[14]||'',new Date().toISOString(),p.deletedBy||'',row[15]||'']));
          kuka.deleteRow(i+1);
          result={status:'ok',version:VERSION};break;
        }
      }
      if (!result) result={status:'ok',msg:'not found',version:VERSION};
    }
    else if (action === 'loadDocTrash' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const sh = ss.getSheetByName('Dokumentumok_Kuka');
      if(!sh){result={status:'ok',version:VERSION,data:[]};} else {
        const vals=sh.getDataRange().getValues();
        const rows=vals.slice(1).map(r=>({
          id:String(r[0]),title:String(r[1]),desc:String(r[2]),
          tags:String(r[3]),uploader:String(r[4]),uploaded:String(r[5]),
          files:String(r[6]),deletedAt:String(r[10]),deletedBy:String(r[11]),tanev:String(r[12])
        })).filter(r=>r.id&&r.id!=='id');
        result={status:'ok',version:VERSION,data:rows};
      }
    }
    else if (action === 'restoreDoc' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const kuka = ss.getSheetByName('Dokumentumok_Kuka');
      if(kuka){
        const vals=kuka.getRange('A:A').getValues();
        for(let i=vals.length-1;i>=1;i--){
          if(String(vals[i][0])===String(p.id)){
            const row=kuka.getRange(i+1,1,1,10).getValues()[0];
            const tanev=p.tanev||getActiveTanev(ss);
            const sh=getDocsSheet(ss,tanev);
            sh.appendRow(sanitize([String(Date.now()),row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9]]));
            kuka.deleteRow(i+1);
            result={status:'ok',version:VERSION};break;
          }
        }
      }
      if(!result)result={status:'ok',msg:'not found',version:VERSION};
    }
    else if (action === 'permDeleteDoc' && sheetId) {
      const ss = SpreadsheetApp.openById(sheetId);
      const kuka = ss.getSheetByName('Dokumentumok_Kuka');
      if(kuka){
        const vals=kuka.getRange('A:A').getValues();
        for(let i=vals.length-1;i>=1;i--){
          if(String(vals[i][0])===String(p.id)){kuka.deleteRow(i+1);result={status:'ok',version:VERSION};break;}
        }
      }
      if(!result)result={status:'ok',msg:'not found',version:VERSION};
    }
    else {
      result = {status:'unknown',action,version:VERSION};
    }

    return makeResponse(result, cb);
  } catch(err) {
    return makeResponse({status:'error',message:err.toString(),version:VERSION}, e.parameter.callback);
  }
}

function doPost(e) {
  return makeResponse({status:'ok',msg:'use GET',version:VERSION}, null);
}

function doPost(e) {
  try {
    // Parse JSON body and merge with URL params
    let body = {};
    if (e.postData && e.postData.contents) {
      body = JSON.parse(e.postData.contents);
    }
    // Create fake event with merged params
    const merged = Object.assign({}, e.parameter, body);
    const fakeE = {parameter: merged};
    return doGet(fakeE);
  } catch(err) {
    return ContentService.createTextOutput(
      JSON.stringify({status:'error', message:err.toString(), version:VERSION})
    ).setMimeType(ContentService.MimeType.JSON);
  }
}
