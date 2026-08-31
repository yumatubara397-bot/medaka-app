"""保存先フォルダ：登録するとフォルダが自動でできるか、そこから読み込めるかを検証する。
   ブラウザのフォルダ選択ダイアログは自動で押せないので、
   showDirectoryPicker を「本物と同じ動きをする偽物」に差し替えて確かめる。"""
import time, os, shutil, glob
from common import Browser, Report

ROOT = "/tmp/medaka_fish_root"
shutil.rmtree(ROOT, ignore_errors=True); os.makedirs(ROOT)

b = Browser(9355, 1200, 1200); r = Report()

# 本物と同じ作りの、メモリ上のフォルダを用意する（作られたものは window.__fs で覗ける）
b.ev("""
window.__fs = { name:'魚', dirs:{} };
function makeDir(name, store){
  return {
    kind:'directory', name,
    async getDirectoryHandle(n, opt){
      if(!store[n]){
        if(!opt || !opt.create){ const e=new Error('NotFound'); e.name='NotFoundError'; throw e; }
        store[n] = { files:{}, dirs:{} };
      }
      return makeSub(n, store[n]);
    },
    async queryPermission(){ return 'granted'; },
    async requestPermission(){ return 'granted'; }
  };
}
function makeSub(name, node){
  return {
    kind:'directory', name,
    async getDirectoryHandle(n,opt){ if(!node.dirs[n]){ if(!opt||!opt.create) throw Object.assign(new Error('x'),{name:'NotFoundError'}); node.dirs[n]={files:{},dirs:{}};} return makeSub(n,node.dirs[n]); },
    async *entries(){
      for(const [fn, blob] of Object.entries(node.files)){
        yield [fn, { kind:'file', name:fn, getFile: async () => blob }];
      }
    },
    __node: node
  };
}
window.__rootHandle = makeDir('魚', window.__fs.dirs);
window.showDirectoryPicker = async () => window.__rootHandle;
""")
time.sleep(0.3)
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(0.8)

print("■ 保存先を選ぶ")
r.expect("最初は案内が出る", "保存先を選ぶ" in (b.ev("document.getElementById('regFsBar').textContent") or ""),
         (b.ev("document.getElementById('regFsBar').textContent") or "").strip()[:60])
b.ev("fsChooseRoot()"); time.sleep(1.0)
r.expect("選ぶと保存先が出る", "魚" in (b.ev("document.getElementById('regFsBar').textContent") or ""),
         (b.ev("document.getElementById('regFsBar').textContent") or "").strip()[:70])
r.check("覚えている名前", b.ev("localStorage.getItem('medaka_fs_root_name')"), "魚")

print("■ 登録するとフォルダができる")
b.ev("""{ TepraLink._kind='none';
  [['幹之','特上'],['夜桜','上物']].forEach(([nm,rk])=>{
    regSel.breed=regMasters().breeds.find(x=>x.name===nm);
    regSel.rank=rk; regSel.qtyMode='pair'; regSel.qtyN=1; regSel.step=3; regDoRegister(); }); }""")
time.sleep(1.5)
made = b.ev("Object.keys(window.__fs.dirs)")
r.check("2つできた", len(made or []), 2)
no1 = b.ev("regItems()[0].controlNo")
r.expect("名前は 管理番号_品種名", (no1 + "_幹之") in (made or []), str(made))
r.expect("2件目も同じ形", any(x.endswith("_夜桜") for x in (made or [])), str(made))

print("■ フォルダ名に使えない文字は落とす")
b.ev("regAddBreed('赤/白:ラメ','あかしろらめ','')")
b.ev("regSel.breed=regMasters().breeds.find(x=>x.name==='赤/白:ラメ');regSel.step=3;regDoRegister()")
time.sleep(1.2)
made = b.ev("Object.keys(window.__fs.dirs)")
r.expect("スラッシュとコロンが _ になる", any("赤_白_ラメ" in x for x in (made or [])), str(made))

print("■ 足りないフォルダをまとめて作る")
b.ev("delete window.__fs.dirs[Object.keys(window.__fs.dirs)[0]]")
r.check("1つ消した", len(b.ev("Object.keys(window.__fs.dirs)") or []), 2)
b.ev("fsCreateMissingFolders()"); time.sleep(1.2)
r.check("作り直される", len(b.ev("Object.keys(window.__fs.dirs)") or []), 3)

print("■ フォルダに入れた写真を読み込む")
b.ev("""{ const mk=(c)=>{const cv=document.createElement('canvas');cv.width=cv.height=80;
    const x=cv.getContext('2d');x.fillStyle=c;x.fillRect(0,0,80,80);
    return new Promise(res=>cv.toBlob(res,'image/jpeg')); };
  window.__put = async (dir, names, col) => {
    const blob = await mk(col);
    names.forEach(n => { window.__fs.dirs[dir].files[n] = blob; });
  }; }""")
keys = b.ev("Object.keys(window.__fs.dirs).sort()")
b.ev(f"__put({keys[0]!r}, ['b.jpg','a.jpg','c.jpg'], '#2b6cb0')"); time.sleep(0.4)
b.ev(f"__put({keys[1]!r}, ['x.jpg','y.jpg'], '#2f855a')"); time.sleep(0.4)
b.ev("switchTab('import');fsLoadFromFolders()"); time.sleep(2.5)
r.check("商品は3件", b.ev("products.length"), 3)
counts = b.ev("JSON.stringify(products.map(p=>p.specimenIdxs.length))")
r.expect("写真の入ったフォルダぶんだけ読める", counts in ('[3,2,0]','[0,3,2]','[2,3,0]','[3,0,2]','[2,0,3]','[0,2,3]'), counts)
r.check("合計5枚", b.ev("photos.length"), 5)
r.expect("名前順に並ぶ",
         b.ev("JSON.stringify(products.filter(p=>p.specimenIdxs.length===3).map(p=>p.specimenIdxs.map(i=>photos[i].name))[0])") == '["a.jpg","b.jpg","c.jpg"]',
         b.ev("JSON.stringify(products.filter(p=>p.specimenIdxs.length===3).map(p=>p.specimenIdxs.map(i=>photos[i].name))[0])"))
r.check("フォルダ表示も3つ", b.ev("document.querySelectorAll('#folderList .folder').length"), 3)
r.expect("撮り忘れが分かる",
         "写真がありません" in (b.ev("document.getElementById('folderList').textContent") or ""), "写真0枚のフォルダを表示")

print("■ 順番に頼らない")
r.expect("撮った順ではなくフォルダで決まる",
         b.ev("products.every(p=>p.specimenIdxs.every(i=>photos[i]))"), "各商品の写真が自分のフォルダのもの")

b.close(); r.finish()
