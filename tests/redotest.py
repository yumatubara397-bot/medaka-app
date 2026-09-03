"""拡大表示と「1枚だけやり直す」を検証する。"""
import time
from common import Browser, Report

b = Browser(9359, 1300, 1200); r = Report()
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(0.8)
b.ev("""{ TepraLink._kind='none';
  [['幹之','特上'],['夜桜','上物']].forEach(([nm,rk])=>{
    regSel.breed=regMasters().breeds.find(x=>x.name===nm);
    regSel.rank=rk; regSel.qtyMode='pair'; regSel.qtyN=1; regSel.step=4; regDoRegister(); }); }""")
time.sleep(1.2)
b.ev("""(async()=>{ const mk=(c)=>{const cv=document.createElement('canvas');cv.width=600;cv.height=400;
   const x=cv.getContext('2d');x.fillStyle=c;x.fillRect(0,0,600,400);
   return new Promise(res=>cv.toBlob(res,'image/jpeg',0.9)); };
  const cols=['#2b6cb0','#2f855a','#b7791f','#9b2c2c','#553c9a','#0987a0'];
  photos=[]; for(let i=0;i<6;i++){ const bl=await mk(cols[i]);
    photos.push({name:'IMG_'+String(i+1)+'.jpg', handle:{getFile:async()=>bl}, blobUrl:URL.createObjectURL(bl)}); }
  folderHandle={name:'テスト'}; })()""")
time.sleep(1.5)
b.ev("switchTab('import');document.getElementById('assignPerItem').value=3;refreshAssignBar();assignPhotosToRegistered()")
time.sleep(1.5)

print("■ フォルダの写真を押すと拡大する")
r.expect("拡大できる印がついている", b.ev("!!document.querySelector('#folderList .shot[data-action=zoom]')"), "zoom-in")
b.ev("document.querySelectorAll('#folderList .shot')[1].click()"); time.sleep(0.8)
r.expect("拡大画面が開く", not b.ev("document.getElementById('lightbox').classList.contains('hidden')"), "")
r.check("2枚目を見ている", b.ev("photos[lbState.photoIdxs[lbState.pos]].name"), "IMG_2.jpg")

print("■ 拡大・縮小・送り")
z0 = b.ev("lbState.zoom")
b.ev("document.getElementById('lbZoomIn').click()"); time.sleep(0.3)
r.expect("拡大できる", b.ev("lbState.zoom") > z0, f"{z0} → {b.ev('lbState.zoom')}")
b.ev("document.getElementById('lbZoomOut').click()"); time.sleep(0.3)
b.ev("document.getElementById('lbNext').click()"); time.sleep(0.5)
r.check("次の写真へ", b.ev("photos[lbState.photoIdxs[lbState.pos]].name"), "IMG_3.jpg")
b.ev("document.getElementById('lbPrev').click()"); time.sleep(0.5)
r.check("前へ戻る", b.ev("photos[lbState.photoIdxs[lbState.pos]].name"), "IMG_2.jpg")

print("■ やり直しの画面")
r.expect("やり直すボタンがある", b.ev("!!document.getElementById('lbRedo')"), "↺ やり直す")
b.ev("document.getElementById('lbRedo').click()"); time.sleep(0.8)
r.expect("やり直し画面が開く", not b.ev("document.getElementById('redoDialog').classList.contains('hidden')"), "")
r.expect("対象の写真名が出る", "IMG_2.jpg" in (b.ev("document.getElementById('redoDialog').textContent") or ""),
         (b.ev("document.getElementById('redoDialog').textContent") or "").replace("\n"," ")[:70])
r.expect("管理番号と品種が出る", "幹之" in (b.ev("document.getElementById('redoDialog').textContent") or ""), "幹之")
r.check("理由の選択肢がある", b.ev("document.querySelectorAll('.redo-chip').length"), 9)
r.expect("撮り直すはAndroidだけ", not b.ev("!!document.getElementById('redoShoot')"), "パソコンなので出ない")

print("■ 理由を選んで「使わない」")
b.ev("[...document.querySelectorAll('.redo-chip')].find(x=>x.textContent==='ピントが合っていない').click()"); time.sleep(0.3)
b.ev("[...document.querySelectorAll('.redo-chip')].find(x=>x.textContent==='暗い').click()"); time.sleep(0.3)
b.ev("document.getElementById('redoFree').value='容器のふちが写っている'")
b.ev("document.getElementById('redoDrop').click()"); time.sleep(1.0)
r.check("その写真だけ外れる", b.ev("products[0].specimenIdxs.length"), 2)
r.expect("外れたのは2枚目", b.ev("products[0].specimenIdxs.map(i=>photos[i].name).join(',')") == "IMG_1.jpg,IMG_3.jpg",
         b.ev("products[0].specimenIdxs.map(i=>photos[i].name).join(',')"))
r.check("もう1件は減らない", b.ev("products[1].specimenIdxs.length"), 3)
r.expect("拡大画面もやり直し画面も閉じる",
         b.ev("document.getElementById('lightbox').classList.contains('hidden')")
         and b.ev("document.getElementById('redoDialog').classList.contains('hidden')"), "")
r.check("フォルダの枚数表示も変わる",
        b.ev("document.querySelectorAll('#folderList .folder')[0].querySelector('.cnt').textContent"), "2枚")

print("■ ダメだった理由を覚えている")
log = b.ev("redoLog().map(x=>x.text)")
r.check("3つ記録される", len(log or []), 3)
r.expect("選んだ理由と自由記入が入る",
         set(log or []) == {"ピントが合っていない","暗い","容器のふちが写っている"}, str(log))
r.expect("どの商品の写真かも残る",
         (b.ev("redoLog()[0].controlNo") or "").startswith("MD-") and b.ev("redoLog()[0].photo") == "IMG_2.jpg",
         b.ev("redoLog()[0].controlNo") + " / " + str(b.ev("redoLog()[0].photo")))

print("■ 次のAI編集に活かす")
notes = b.ev("aiNotes().map(x=>x.text)")
r.expect("AIへの指示にも足される",
         set(["ピントが合っていない","暗い","容器のふちが写っている"]).issubset(set(notes or [])), str(notes))
prompt = b.ev("buildAiPrompt('', '黒')")
r.expect("AIのお願い文に反映される", "暗い" in (prompt or ""), 
         (prompt or "")[-160:].replace("\n"," "))

print("■ よくある理由をまとめて出す")
b.ev("addRedoReason('暗い',{controlNo:'X',photo:'y.jpg'})"); time.sleep(0.2)
top = b.ev("redoTopReasons(3)")
r.expect("多い順に出る", top and top[0][0] == "暗い" and top[0][1] == 2, str(top))

b.close(); r.finish()
