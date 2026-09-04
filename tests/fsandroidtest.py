"""Android経路：アプリの窓口(FolderBridge)を偽物に差し替えて、
   登録→フォルダ作成→撮影／写真追加→読み込み までを確かめる。"""
import time
from common import Browser, Report

b = Browser(9356, 1200, 1300); r = Report()

# Androidアプリの窓口を真似る（作られたフォルダと写真は window.__fb で覗ける）
b.ev("""
window.__fb = { root:null, dirs:{}, calls:[] };
function mkJpegBase64(){
  const cv=document.createElement('canvas'); cv.width=cv.height=40;
  const x=cv.getContext('2d'); x.fillStyle='#3182ce'; x.fillRect(0,0,40,40);
  return cv.toDataURL('image/jpeg').split(',')[1];
}
window.FolderBridge = {
  status(){ return JSON.stringify({ok:true, supported:true, hasRoot:!!__fb.root, rootName:__fb.root||''}); },
  chooseRoot(){ __fb.root='魚'; return JSON.stringify({ok:true, supported:true, hasRoot:true, rootName:'魚'}); },
  ensureFolder(name){ __fb.calls.push('ensure:'+name); if(!__fb.dirs[name]) __fb.dirs[name]=[]; return JSON.stringify({ok:true}); },
  listPhotos(name){ return JSON.stringify({ok:true, files:(__fb.dirs[name]||[]).slice().sort()}); },
  readPhoto(name, file, maxEdge){ __fb.calls.push('read:'+name+'/'+file+'@'+maxEdge);
    return JSON.stringify({ok:true, base64: mkJpegBase64()}); },
  takePhoto(name, file){ __fb.calls.push('shoot:'+name+'/'+file);
    (__fb.dirs[name] = __fb.dirs[name]||[]).push(file); return JSON.stringify({ok:true}); },
  addFromGallery(name, prefix){ const d=(__fb.dirs[name]=__fb.dirs[name]||[]);
    d.push(prefix+'_'+String(d.length+1).padStart(2,'0')+'.jpg');
    d.push(prefix+'_'+String(d.length+1).padStart(2,'0')+'.jpg');
    return JSON.stringify({ok:true, added:2}); }
};
""")
time.sleep(0.3)
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(1.0)

print("■ 端末の判定")
r.check("Android経路", b.ev("FsLink.kind()"), "android")
r.expect("最初は保存先を選ぶ案内", "保存先を選ぶ" in (b.ev("document.getElementById('regFsBar').textContent") or ""),
         (b.ev("document.getElementById('regFsBar').textContent") or "").strip()[:60])

print("■ 保存先を選ぶ")
b.ev("FsLink.chooseRoot()"); time.sleep(1.0)
r.expect("保存先が出る", "魚" in (b.ev("document.getElementById('regFsBar').textContent") or ""),
         (b.ev("document.getElementById('regFsBar').textContent") or "").strip()[:70])

print("■ 登録するとフォルダができる")
b.ev("""{ TepraLink._kind='none';
  [['幹之','特上'],['夜桜','上物']].forEach(([nm,rk])=>{
    regSel.breed=regMasters().breeds.find(x=>x.name===nm);
    regSel.rank=rk; regSel.qtyMode='pair'; regSel.qtyN=1; regSel.step=4; regDoRegister(); }); }""")
time.sleep(1.5)
dirs = b.ev("Object.keys(window.__fb.dirs)")
r.check("2つできた", len(dirs or []), 2)
no1 = b.ev("regItems()[0].controlNo")
r.expect("名前は 魚名_管理番号", ("幹之_" + no1) in (dirs or []), str(dirs))

print("■ 取込タブでフォルダが並ぶ")
b.ev("switchTab('edit');fsLoadAuto()"); time.sleep(2.0)
r.check("フォルダ2つ", b.ev("document.querySelectorAll('#folderList .folder').length"), 2)
r.expect("撮影ボタンが出る", b.ev("!!document.querySelector('#folderList [data-act=shoot]')"), "📷 撮る")
r.expect("写真追加ボタンも出る", b.ev("!!document.querySelector('#folderList [data-act=gallery]')"), "🖼 写真から追加")
r.expect("まだ写真は無い", "写真がありません" in (b.ev("document.getElementById('folderList').textContent") or ""), "")

print("■ その場で撮る")
b.ev("document.querySelectorAll('#folderList [data-act=shoot]')[0].click()"); time.sleep(2.5)
key = "幹之_" + no1
r.check("1枚保存された", len(b.ev("window.__fb.dirs[" + repr(key) + "]") or []), 1)
first = b.ev("window.__fb.dirs[" + repr(key) + "][0]")
r.expect("名前は 管理番号_01.jpg", first == no1 + "_01.jpg", str(first))
r.check("読み込まれて1枚になる", b.ev("products[0].specimenIdxs.length"), 1)
r.check("画面のこまも1枚", b.ev("document.querySelectorAll('#folderList .folder')[0].querySelectorAll('.shot').length"), 1)

print("■ 写真から追加")
b.ev("document.querySelectorAll('#folderList [data-act=gallery]')[1].click()"); time.sleep(2.5)
r.check("2枚目のフォルダに2枚", b.ev("products[1].specimenIdxs.length"), 2)
r.check("合計3枚", b.ev("photos.length"), 3)

print("■ 続けて撮ると番号が増える")
b.ev("document.querySelectorAll('#folderList [data-act=shoot]')[0].click()"); time.sleep(2.5)
names = b.ev("window.__fb.dirs[" + repr(key) + "]")
r.check("2枚になる", len(names or []), 2)
r.expect("_02.jpg が増える", (names or [])[-1] == no1 + "_02.jpg", str(names))

print("■ 読み込みは縮めてから渡している")
r.expect("長辺1600を指定している",
         any("@1600" in c for c in (b.ev("window.__fb.calls") or [])),
         [c for c in (b.ev("window.__fb.calls") or []) if c.startswith("read:")][:2])

print("■ 出品用のタイトルもできる")
t = b.ev("buildTitle(products[0], {})")
r.expect("品種と管理番号が入る", "幹之" in (t or "") and (no1 in (t or "")), t)

b.close(); r.finish()
