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

print("■ 撮ったものは、押すまで保存されない")
b.ev("""
  const f = new File([new Blob(['x'])], 'IMG_001.JPG', {type:'image/jpeg'});
  Cam.addFiles([f]); 'ok'"""); time.sleep(0.4)
r.check("手元に1枚ある", b.ev("Cam.pending.length"), 1)
r.check("まだフォルダには入っていない", b.ev("Object.keys(window.__dir._files).length"), 0)
r.expect("保存先が出る", "編集前 / 幹之_MD-260905-001" in (b.ev("document.getElementById('camDest').textContent") or ""),
         b.ev("document.getElementById('camDest').textContent"))
r.check("保存ボタンに枚数が出る", b.ev("document.getElementById('camSave').textContent"), "💾 1枚を保存する")

print("■ ×ですぐ消せる")
b.ev("""Cam.addFiles([new File([new Blob(['y'])], 'a.png', {type:'image/png'}),
                     new File([new Blob(['z'])], 'b.jpeg', {type:'image/jpeg'})]); 'ok'""")
time.sleep(0.3)
r.check("3枚ためた", b.ev("Cam.pending.length"), 3)
r.check("×ボタンも3つ", b.ev("document.querySelectorAll('#camShots .x').length"), 3)
b.ev("document.querySelectorAll('#camShots .x')[1].click()"); time.sleep(0.3)
r.check("押した1枚だけ消える", b.ev("Cam.pending.length"), 2)
r.check("残ったのは1枚目と3枚目", b.ev("Cam.pending.map(p=>p.ext).join(',')"), "jpg,jpg")
r.check("番号が振り直される", b.ev("[...document.querySelectorAll('#camShots .n')].map(e=>e.textContent).join(',')"), "1,2")
r.check("消してもフォルダは空のまま", b.ev("Object.keys(window.__dir._files).length"), 0)

print("■ 保存するボタンで、そのフォルダに入る")
b.ev("(async()=>{ await Cam.saveAll(); })()"); time.sleep(0.6)
r.check("2枚入る", b.ev("Object.keys(window.__dir._files).length"), 2)
r.check("管理番号＋連番の名前になる",
        b.ev("Object.keys(window.__dir._files).sort().join(',')"),
        "MD-260905-001_01.jpg,MD-260905-001_02.jpg")
r.check("手元は空になる", b.ev("Cam.pending.length"), 0)
r.expect("保存の帯が消える", b.ev("document.getElementById('camSaveBar').classList.contains('hidden')"), "hidden")

print("■ 続けて撮ると番号が続く")
b.ev("""Cam.addFiles([new File([new Blob(['w'])], 'c.jpg', {type:'image/jpeg'})]); 'ok'""")
b.ev("(async()=>{ await Cam.saveAll(); })()"); time.sleep(0.5)
r.check("3枚目は _03", b.ev("Object.keys(window.__dir._files).sort().join(',')"),
        "MD-260905-001_01.jpg,MD-260905-001_02.jpg,MD-260905-001_03.jpg")

print("■ シャッター音")
r.expect("音を鳴らす仕掛けがある", b.ev("typeof camShutterSound"), "function")
r.expect("音のファイルを持たずに鳴らす",
         b.ev("(()=>{ try{ camShutterSound(); return 'ok'; }catch(e){ return 'ERR '+e.message; } })()") == 'ok',
         "その場で作る")

print("■ すでに写真が入っているフォルダでも、上書きしない")
b.ev("window.__dir2 = fakeDir('夜桜_MD-9', {'MD-9_01.jpg':1, 'MD-9_07.jpg':1}); 'ok'")
r.check("次は8番から", b.ev("(async()=>await Cam.nextIndex(window.__dir2))()"), 8)

print("■ 保存が済めば手元は空になる")
r.check("並びも空になる", b.ev("document.querySelectorAll('#camShots .cam-shot').length"), 0)

print("■ 終わると片付く")
b.ev("Cam.close()"); time.sleep(0.4)
r.expect("画面が閉じる", b.ev("document.getElementById('camDialog').classList.contains('hidden')"), "hidden")
r.check("カメラを止める", b.ev("Cam.stream"), None)

print("■ 「写真を撮る」は編集タブに飛ばさない")
b.ev("""localStorage.setItem('medaka_reg_items', JSON.stringify([
  {variety:'幹之', rank:'特上', quantityText:'3ペア', controlNo:'MD-260905-001'}]));
regSel.lastNo = 'MD-260905-001'; renderRegDone();
window.__realOpen = Cam.open;
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

print("■ 保存せずに閉じようとしたとき")
b.ev("Cam.open = window.__realOpen")     # 本物に戻す
b.ev("""window.__dir3 = fakeDir('夜桜_MD-7', {});
fsEnsureFolder = async () => window.__dir3;
window.__item3 = {variety:'夜桜', rank:'上物', quantityText:'2ペア', controlNo:'MD-7'};
'ok'""")
b.ev("(async()=>{ await Cam.open(window.__item3); })()"); time.sleep(0.5)
b.ev("Cam.addFiles([new File([new Blob(['q'])], 'q.jpg', {type:'image/jpeg'})]); 'ok'"); time.sleep(0.3)
r.check("手元に1枚", b.ev("Cam.pending.length"), 1)

# キャンセル → 閉じない、消えない
b.ev("window.confirm = () => false")
b.ev("(async()=>{ await Cam.close(); })()"); time.sleep(0.4)
r.expect("キャンセルなら閉じない",
         not b.ev("document.getElementById('camDialog').classList.contains('hidden')"), "開いたまま")
r.check("写真も消えない", b.ev("Cam.pending.length"), 1)

# OK → 保存してから閉じる
b.ev("window.confirm = () => true")
b.ev("(async()=>{ await Cam.close(); })()"); time.sleep(0.6)
r.expect("OKなら閉じる", b.ev("document.getElementById('camDialog').classList.contains('hidden')"), "hidden")
r.check("捨てずに保存されている", b.ev("Object.keys(window.__dir3._files).join(',')"), "MD-7_01.jpg")
r.check("手元は空", b.ev("Cam.pending.length"), 0)

b.close(); r.finish()
