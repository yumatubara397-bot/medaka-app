# -*- coding: utf-8 -*-
"""「写真を撮る」を押したら、その場でカメラが立ち上がり、
   撮った写真がその商品のフォルダに保存されるかを確かめる。"""
import time
from common import Browser, Report

b = Browser(9400, 1200, 1000); r = Report()
b.ev("localStorage.clear()"); time.sleep(0.4)

# にせのフォルダ（書き込みを記録する）
b.ev(r"""
function fakeDir(name, files){
  files = files || {};
  return { kind:'directory', name:name, _files:files,
    async getFileHandle(n, o){
      if(!(n in files)){ if(!o||!o.create){ const e=new Error('nf'); e.name='NotFoundError'; throw e; } files[n]=null; }
      return { async createWritable(){ return { async write(b){ files[n]=b; }, async close(){} }; },
               async getFile(){ return files[n]; } };
    },
    entries(){ const l=Object.entries(files); let i=0;
      return { [Symbol.asyncIterator](){return this;},
        async next(){ return i<l.length ? {value:[l[i][0], {kind:'file', name:l[i++][0]}], done:false} : {done:true}; } }; }
  };
}
window.__dir = fakeDir('幹之_MD-260905-001', {});
fsEnsureFolder = async () => window.__dir;
window.__item = { variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-260905-001' };
'ok'""")

print("■ カメラが使えないときも、理由が出て写真は入れられる")
b.ev("""
navigator.mediaDevices.getUserMedia = async () => {
  const e = new Error('no'); e.name = 'NotAllowedError'; throw e; };
'ok'""")
b.ev("(async()=>{ await Cam.open(window.__item); })()"); time.sleep(0.6)
r.expect("撮影画面が開く", not b.ev("document.getElementById('camDialog').classList.contains('hidden')"), "camDialog 表示")
r.check("どの商品か出る", b.ev("document.getElementById('camNo').textContent"), "MD-260905-001")
r.expect("保存先も出る", "編集前/幹之_MD-260905-001/" in (b.ev("document.getElementById('camSub').textContent") or ""),
         b.ev("document.getElementById('camSub').textContent"))
msg = b.ev("document.getElementById('camMsg').textContent") or ""
r.expect("許可が無い理由が出る", "許可" in msg, msg[:60])
r.expect("ファイルからも入れられると伝える", "ファイルから追加" in msg, "代わりの道を示す")

print("■ ファイルから足すと、その商品のフォルダに入る")
b.ev("""(async()=>{
  const f = new File([new Blob(['x'])], 'IMG_001.JPG', {type:'image/jpeg'});
  await Cam.addFiles([f]);
})()"""); time.sleep(0.5)
r.check("1枚入る", b.ev("Object.keys(window.__dir._files).length"), 1)
r.check("管理番号＋連番の名前になる", b.ev("Object.keys(window.__dir._files)[0]"), "MD-260905-001_01.jpg")

print("■ 続けて足すと番号が増える")
b.ev("""(async()=>{
  await Cam.addFiles([new File([new Blob(['y'])], 'a.png', {type:'image/png'}),
                      new File([new Blob(['z'])], 'b.jpeg', {type:'image/jpeg'})]);
})()"""); time.sleep(0.5)
r.check("3枚になる", b.ev("Object.keys(window.__dir._files).length"), 3)
r.check("番号が続く", b.ev("Object.keys(window.__dir._files).sort().join(',')"),
        "MD-260905-001_01.jpg,MD-260905-001_02.png,MD-260905-001_03.jpg")

print("■ すでに写真が入っているフォルダでも、上書きしない")
b.ev("window.__dir2 = fakeDir('夜桜_MD-9', {'MD-9_01.jpg':1, 'MD-9_07.jpg':1}); 'ok'")
r.check("次は8番から", b.ev("(async()=>await Cam.nextIndex(window.__dir2))()"), 8)

print("■ 撮った枚数の見た目")
r.check("撮った写真が並ぶ", b.ev("document.querySelectorAll('#camShots img').length"), 3)

print("■ 終わると片付く")
b.ev("Cam.close()"); time.sleep(0.4)
r.expect("画面が閉じる", b.ev("document.getElementById('camDialog').classList.contains('hidden')"), "hidden")
r.check("カメラを止める", b.ev("Cam.stream"), None)

print("■ 「写真を撮る」は編集タブに飛ばさない")
b.ev("""localStorage.setItem('medaka_reg_items', JSON.stringify([
  {variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-260905-001'}]));
regSel.lastNo = 'MD-260905-001'; renderRegDone();
window.__opened = null; Cam.open = async (it) => { window.__opened = it.controlNo; };
'ok'""")
time.sleep(0.3)
r.check("ボタンの文言", b.ev("document.getElementById('regGoPhotos').textContent"), "📷 写真を撮る")
b.ev("document.getElementById('regGoPhotos').click()"); time.sleep(0.4)
r.check("押すとカメラが開く", b.ev("window.__opened"), "MD-260905-001")
r.expect("編集タブに移らない",
         b.ev("document.getElementById('panel-register').classList.contains('hidden')") == False,
         "登録タブのまま")

print("■ 登録一覧からも撮れる")
b.ev("""localStorage.setItem('medaka_reg_items', JSON.stringify([
  {variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-260905-001'},
  {variety:'舞めだかゴールドフード', rank:'', quantityText:'1個', controlNo:'YO-01', kind:'goods'}
])); renderRegItems(); 'ok'""")
time.sleep(0.4)
r.check("メダカにはカメラボタンが付く", b.ev("document.querySelectorAll('#regItemList .cam').length"), 1)
r.expect("用品には付かない",
         b.ev("!!document.querySelector('#regItemList .reg-item.goods .cam')") == False,
         "用品は撮らない")
b.ev("window.__opened = null; document.querySelector('#regItemList .cam').click()"); time.sleep(0.4)
r.check("押すとその商品のカメラが開く", b.ev("window.__opened"), "MD-260905-001")

print("■ どのカメラを使うかの選び分け")
def choose(devs, saved="null"):
    import json
    return b.ev(f"(camChoose({devs}, {saved})||{{}}).label")

r.check("外側(Rear)を選ぶ",
        choose("[{deviceId:'a',label:'Surface Camera Front'},{deviceId:'b',label:'Surface Camera Rear'}]"),
        "Surface Camera Rear")
r.check("Back という名前でも選ぶ",
        choose("[{deviceId:'a',label:'Integrated Webcam (Front)'},{deviceId:'b',label:'Back Camera'}]"),
        "Back Camera")
r.check("日本語の「背面」も選ぶ",
        choose("[{deviceId:'a',label:'前面カメラ'},{deviceId:'b',label:'背面カメラ'}]"), "背面カメラ")
r.check("外側と分かる名前が無ければ、内側でないものを選ぶ",
        choose("[{deviceId:'a',label:'HD User Facing'},{deviceId:'b',label:'USB Camera'}]"), "USB Camera")
r.check("名前で分からなければ最後のものを選ぶ",
        choose("[{deviceId:'a',label:''},{deviceId:'b',label:''}]"), "")
r.check("前に選んだものがあれば、それを優先する",
        choose("[{deviceId:'a',label:'Front'},{deviceId:'b',label:'Rear'}]", "'a'"), "Front")
r.check("覚えているものが無くなっていたら、選び直す",
        choose("[{deviceId:'a',label:'Front'},{deviceId:'b',label:'Rear'}]", "'zzz'"), "Rear")
r.check("1つしか無ければ、それを使う",
        choose("[{deviceId:'a',label:'Front only'}]"), "Front only")
r.expect("カメラが無ければ null", b.ev("camChoose([], null)") is None, "null")

print("■ 内側／外側の見分け")
for label, back, front in [("Surface Camera Rear", True, False), ("Front Camera", False, True),
                           ("背面カメラ", True, False), ("前面カメラ", False, True),
                           ("USB Video Device", False, False),
                           ("Surface Camera Front", False, True),
                           ("Microsoft Camera Rear", True, False),
                           ("Surface Hub Camera", False, False)]:
    r.check(f"{label} → 外側", b.ev(f"camIsBack({label!r})"), back)
    r.check(f"{label} → 内側", b.ev(f"camIsFront({label!r})"), front)

b.close(); r.finish()
