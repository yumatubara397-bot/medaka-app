"""登録 → 編集前フォルダ → 編集タブで自動読み込み → 編集を終えて編集後へ、を通しで確かめる。"""
import time, json
from common import Browser, Report

b = Browser(9382, 1200, 1100); r = Report()
# デスクトップ（親フォルダ）を真似る。中の 編集前 / 編集後 を使う
b.ev("""
window.__fs = { name:'デスクトップ', dirs:{} };
function node(){ return { files:{}, dirs:{} }; }
function mkdir(name, store){
  return {
    kind:'directory', name,
    async getDirectoryHandle(n, opt){
      if(!store[n]){ if(!opt||!opt.create){ const e=new Error('x'); e.name='NotFoundError'; throw e; } store[n]=node(); }
      return sub(n, store[n]);
    },
    async queryPermission(){ return 'granted'; },
    async requestPermission(){ return 'granted'; }
  };
}
function sub(name, nd){
  return {
    kind:'directory', name, __node: nd,
    async getDirectoryHandle(n,opt){ if(!nd.dirs[n]){ if(!opt||!opt.create){const e=new Error('x');e.name='NotFoundError';throw e;} nd.dirs[n]=node(); } return sub(n,nd.dirs[n]); },
    async getFileHandle(n,opt){ if(!(n in nd.files)){ if(!opt||!opt.create){const e=new Error('x');e.name='NotFoundError';throw e;} nd.files[n]=null; }
      return { async createWritable(){ return { async write(b){ nd.files[n]=b; }, async close(){} }; },
               async getFile(){ return nd.files[n]; } }; },
    async removeEntry(n, opt){ delete nd.dirs[n]; delete nd.files[n]; },
    async *entries(){
      for(const [dn, dv] of Object.entries(nd.dirs)) yield [dn, sub(dn, dv)];
      for(const [fn, bl] of Object.entries(nd.files)) yield [fn, {kind:'file', name:fn, getFile: async()=>bl}];
    }
  };
}
window.__rootHandle = mkdir('デスクトップ', window.__fs.dirs);
window.showDirectoryPicker = async () => window.__rootHandle;
window.fsHandleGet = async () => window.__rootHandle;
""")
time.sleep(0.3)
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(1.0)
b.ev("TepraLink._kind='none'; fsChooseRoot()"); time.sleep(1.2)

print("■ 登録すると「編集前」の中にフォルダができる")
b.ev("""{ [['幹之','特上'],['夜桜','上物']].forEach(([nm,rk])=>{
    regSel.mode='fish'; regSel.breed=regMasters().breeds.find(x=>x.name===nm);
    regSel.rank=rk; regSel.qtyMode='pair'; regSel.qtyN=1; regSel.step=4; regDoRegister(); }); }""")
time.sleep(2.0)
top = b.ev("Object.keys(window.__fs.dirs)")
r.expect("「編集前」ができる", "編集前" in (top or []), str(top))
work = b.ev("Object.keys(window.__fs.dirs['編集前'].dirs)")
r.check("2件ぶん", len(work or []), 2)
no1 = b.ev("regItems()[0].controlNo")
r.expect("名前は 品種名_管理番号", ("幹之_" + no1) in (work or []), str(work))

print("■ 写真をフォルダに入れる")
b.ev("""(async()=>{ const mk=(c)=>{const cv=document.createElement('canvas');cv.width=400;cv.height=300;
   const x=cv.getContext('2d');x.fillStyle=c;x.fillRect(0,0,400,300);
   return new Promise(res=>cv.toBlob(res,'image/jpeg',0.9)); };
  const d = window.__fs.dirs['編集前'].dirs;
  const names = Object.keys(d);
  d[names[0]].files['a.jpg'] = await mk('#2b6cb0');
  d[names[0]].files['b.jpg'] = await mk('#2f855a');
  d[names[1]].files['c.jpg'] = await mk('#b7791f'); })()""")
time.sleep(1.5)

print("■ 編集タブを開くと自動で読み込む")
b.ev("products=[]; photos=[]; switchTab('edit')"); time.sleep(3.0)
r.check("商品2件", b.ev("products.length"), 2)
r.check("写真3枚", b.ev("photos.length"), 3)
r.expect("編集の画面になっている", not b.ev("document.getElementById('editLoaded').classList.contains('hidden')"), "")
r.expect("件数が出ている", "3枚" in (b.ev("document.getElementById('editFolderInfo').textContent") or ""),
         b.ev("document.getElementById('editFolderInfo').textContent"))
r.check("フォルダ一覧も出る", b.ev("document.querySelectorAll('#folderList .folder').length"), 2)

print("■ 編集を終えて保存する")
b.ev("window.confirm = () => true")
# 1枚だけ加工したことにする
b.ev("""(async()=>{ const cv=document.createElement('canvas');cv.width=200;cv.height=150;
   const x=cv.getContext('2d');x.fillStyle='#9b2c2c';x.fillRect(0,0,200,150);
   const bl=await new Promise(res=>cv.toBlob(res,'image/jpeg',0.9));
   editState[0]={ editedBlobUrl: URL.createObjectURL(bl), modes:['crop'], showEdited:true }; })()""")
time.sleep(1.0)
b.ev("fsArchiveAll()"); time.sleep(3.5)

top = b.ev("Object.keys(window.__fs.dirs)")
r.expect("「編集後」ができる", "編集後" in (top or []), str(top))
done = b.ev("Object.keys(window.__fs.dirs['編集後'].dirs)")
r.check("2件ぶん保管された", len(done or []), 2)
r.expect("名前は 品種名_管理番号 のまま", any(x.startswith("幹之_") for x in (done or [])), str(done))
sub = b.ev("Object.keys(window.__fs.dirs['編集後'].dirs[Object.keys(window.__fs.dirs['編集後'].dirs)[0]].dirs)")
r.expect("原本と加工後に分かれている", sorted(sub or []) == ["加工後","原本"], str(sub))
org = b.ev("Object.keys(window.__fs.dirs['編集後'].dirs[Object.keys(window.__fs.dirs['編集後'].dirs)[0]].dirs['原本'].files)")
edt = b.ev("Object.keys(window.__fs.dirs['編集後'].dirs[Object.keys(window.__fs.dirs['編集後'].dirs)[0]].dirs['加工後'].files)")
r.expect("原本が入っている", len(org or []) >= 1, str(org))
r.expect("加工後も入っている", len(edt or []) >= 1, str(edt))
r.check("「編集前」の中は空になる", len(b.ev("Object.keys(window.__fs.dirs['編集前'].dirs)") or []), 0)
r.check("登録一覧からも片付く", b.ev("regItems().length"), 0)
r.expect("画面も空に戻る", b.ev("products.length") == 0 and b.ev("photos.length") == 0, "")

print("■ 編集後が無くても自動で作られる")
b.ev("delete window.__fs.dirs['編集後']"); time.sleep(0.3)
r.check("いったん消した", "編集後" in (b.ev("Object.keys(window.__fs.dirs)") or []), False)
b.ev("fsDoneDir()"); time.sleep(1.0)
r.check("呼べば作られる", "編集後" in (b.ev("Object.keys(window.__fs.dirs)") or []), True)

b.close(); r.finish()
