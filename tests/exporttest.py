"""ラベル機能を外したあと、出品CSV+ZIPまで通るかを確かめる。"""
import time, base64, io, zipfile
from common import Browser, Report

b = Browser(9357, 1200, 1200); r = Report()
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(0.8)
b.ev("""{ TepraLink._kind='none';
  [['幹之','特上'],['夜桜','上物']].forEach(([nm,rk])=>{
    regSel.breed=regMasters().breeds.find(x=>x.name===nm);
    regSel.rank=rk; regSel.qtyMode='pair'; regSel.qtyN=2; regSel.step=4; regDoRegister(); }); }""")
time.sleep(1.2)
b.ev("""{ const mk=(c)=>{const cv=document.createElement('canvas');cv.width=800;cv.height=600;
    const x=cv.getContext('2d');x.fillStyle=c;x.fillRect(0,0,800,600);
    return new Promise(res=>cv.toBlob(res,'image/jpeg',0.9)); };
  window.__mk = mk; }""")
b.ev("""(async()=>{ const cols=['#2b6cb0','#2f855a','#b7791f','#9b2c2c','#553c9a','#0987a0'];
  photos=[]; for(let i=0;i<6;i++){ const bl=await window.__mk(cols[i]);
    photos.push({name:'IMG_'+String(i+1).padStart(3,'0')+'.jpg',
      handle:{getFile:async()=>bl}, blobUrl:URL.createObjectURL(bl)}); }
  folderHandle={name:'テスト'}; })()""")
time.sleep(1.5)
b.ev("switchTab('edit'); assignPerItemValue=3; assignPhotosToRegistered(3)")
time.sleep(1.5)

print("■ 写真一覧にラベル切替が無い")
r.check("切替ボタンは0個", b.ev("document.querySelectorAll('.tile-toggle').length"), 0)
r.expect("取込タブは無くなった", not b.ev("!!document.getElementById('panel-import')"), "")
r.check("ラベル扱いの写真は無い", b.ev("photos.filter(p=>p.isLabel).length"), 0)

print("■ 商品と写真")
r.check("商品2件", b.ev("products.length"), 2)
r.check("1件あたり3枚", b.ev("products.every(p=>p.specimenIdxs.length===3)"), True)
r.expect("フォルダ表示に枚数が出る", "3枚" in (b.ev("document.getElementById('folderList').textContent") or ""),
         (b.ev("document.getElementById('folderList').textContent") or "").replace("\n"," ")[:60])

print("■ 出品タブ")
b.ev("switchTab('listing');renderListingPanel()"); time.sleep(1.0)
r.expect("「ラベルを1枚目に」が無い", not b.ev("!!document.getElementById('lstIncludeLabel')"), "")
r.check("出品対象が2件", b.ev("products.length"), 2)

print("■ 出品ファイル（CSV + 画像ZIP）を作る")
b.ev("""{ const cfg = lstConfig(); cfg.CATEGORY_ID='9999999999'; cfg.DURATION='5';
   cfg.END_HOUR='22'; cfg.COUNT='1'; cfg.START_PRICE='1000';
   localStorage.setItem('medaka_lst_config', JSON.stringify(cfg)); }""")
b.ev("window.confirm = () => true; window.__errs=[]; window.__origToast = toast; toast = (m,t)=>{ window.__errs.push(t+':'+m); return window.__origToast(m,t); };")
b.ev("""{ window.__zip=null;
   window.downloadBlob = (blob, name) => { window.__zipName=name;
     const fr=new FileReader(); fr.onload=()=>{ window.__zip=fr.result.split(',')[1]; };
     fr.readAsDataURL(blob); }; }""")
time.sleep(0.3)
b.ev("buildAuctownExport()"); time.sleep(4.0)
name = b.ev("window.__zipName")
r.expect("ZIPができた", bool(b.ev("window.__zip")), str(name) + " / " + str(b.ev("window.__errs"))[:200])
data = b.ev("window.__zip")
if data:
    z = zipfile.ZipFile(io.BytesIO(base64.b64decode(data)))
    names = z.namelist()
    csvs = [n for n in names if n.lower().endswith('.csv')]
    imgs = [n for n in names if n.lower().endswith(('.jpg','.jpeg','.png'))]
    r.expect("CSVが入っている", len(csvs) == 1, str(csvs))
    r.check("画像は6枚（商品2×3枚）", len(imgs), 6)
    csv = z.read(csvs[0]).decode('cp932')
    lines = [l for l in csv.split('\r\n') if l]
    r.check("CSVは見出し+2行", len(lines), 3)
    r.expect("品種と管理番号が入っている", "幹之" in csv and "MD-" in csv, lines[1][:80])
    r.expect("2ペアが入っている", "2ペア" in csv, lines[1][:80])

b.close(); r.finish()
