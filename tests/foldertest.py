"""取込タブ：管理番号ごとのフォルダ表示と、区切りのずらし直しを検証する。"""
import time
from common import Browser, Report

b = Browser(9353, 1200, 1400); r = Report()
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(0.8)

# 3件登録する（テプラは無い前提）
b.ev("""{ TepraLink._kind='none';
  [['幹之','特上'],['夜桜','上物'],['オロチ','通常']].forEach(([nm,rk])=>{
    regSel.breed=regMasters().breeds.find(x=>x.name===nm);
    regSel.rank=rk; regSel.qtyMode='pair'; regSel.qtyN=1; regSel.step=3; regDoRegister(); }); }""")
time.sleep(1.0)
r.check("3件登録した", b.ev("regItems().length"), 3)

print("■ 写真を取り込む前")
b.ev("switchTab('import');renderFolders()"); time.sleep(0.4)
r.expect("案内が出る", "写真を取り込む" in (b.ev("document.getElementById('folderList').textContent") or ""),
         (b.ev("document.getElementById('folderList').textContent") or "").strip()[:50])

print("■ 10枚を1商品3枚で振り分ける")
b.ev("""{ photos = Array.from({length:10},(_,i)=>({name:'IMG_'+String(i+1).padStart(3,'0')+'.jpg',
     handle:{getFile:async()=>new Blob([''],{type:'image/jpeg'})}, blobUrl:null, isLabel:false}));
   folderHandle={name:'テスト'}; }""")
b.ev("document.getElementById('assignPerItem').value=3; refreshAssignBar()"); time.sleep(0.3)
b.ev("assignPhotosToRegistered()"); time.sleep(1.2)
r.check("フォルダが3つ出る", b.ev("document.querySelectorAll('#folderList .folder').length"), 3)
r.check("配分", b.ev("JSON.stringify(products.map(p=>p.specimenIdxs))"), "[[0,1,2],[3,4,5],[6,7,8]]")
r.check("余りは1枚", b.ev("leftoverIdxs.length"), 1)
r.expect("余りの案内が出る", "1枚 余っています" in (b.ev("(document.getElementById('leftoverBox')||{}).textContent||''") or ""),
         (b.ev("(document.getElementById('leftoverBox')||{}).textContent||''") or "")[:50])

print("■ フォルダの見出し（管理番号＋魚名）")
head = b.ev("document.querySelector('#folderList .folder .folder-head').textContent.replace(/\\s+/g,' ').trim()")
r.expect("管理番号が出る", "MD-" in (head or ""), head)
r.expect("品種名が出る", "幹之" in (head or ""), head)
r.expect("ランクと数量も出る", "特上" in (head or "") and "1ペア" in (head or ""), head)
r.expect("枚数が出る", "3枚" in (head or ""), head)
r.check("写真のこまが並ぶ", b.ev("document.querySelectorAll('#folderList .folder')[0].querySelectorAll('.shot').length"), 3)

print("■ ズレを1枚ずつ直せる")
b.ev("document.querySelectorAll('.folder')[0].querySelector('[data-act=plus]').click()"); time.sleep(0.6)
r.check("1枚もらう", b.ev("JSON.stringify(products.map(p=>p.specimenIdxs))"), "[[0,1,2,3],[4,5],[6,7,8]]")
r.check("見出しの枚数も変わる",
        b.ev("document.querySelectorAll('#folderList .folder')[0].querySelector('.cnt').textContent"), "4枚")
b.ev("document.querySelectorAll('.folder')[0].querySelector('[data-act=minus]').click()"); time.sleep(0.6)
r.check("1枚返す", b.ev("JSON.stringify(products.map(p=>p.specimenIdxs))"), "[[0,1,2],[3,4,5],[6,7,8]]")

print("■ 余った写真を最後のフォルダで受け取れる")
r.expect("余りがあるので押せる",
         not b.ev("document.querySelectorAll('.folder')[2].querySelector('[data-act=plus]').disabled"), "余り1枚")
b.ev("document.querySelectorAll('.folder')[2].querySelector('[data-act=plus]').click()"); time.sleep(0.6)
r.check("余りを受け取る", b.ev("JSON.stringify(products.map(p=>p.specimenIdxs))"), "[[0,1,2],[3,4,5],[6,7,8,9]]")
r.check("余りが無くなる", b.ev("leftoverIdxs.length"), 0)
r.expect("余りの案内が消える", not b.ev("!!document.getElementById('leftoverBox')"), "")
r.expect("もらえるものが無ければ押せない",
         b.ev("document.querySelectorAll('.folder')[2].querySelector('[data-act=plus]').disabled"), "")
b.ev("document.querySelectorAll('.folder')[2].querySelector('[data-act=minus]').click()"); time.sleep(0.6)
r.check("手放すと余りに戻る", b.ev("leftoverIdxs.length"), 1)

print("■ 登録側にも写真の枚数が反映される")
r.check("1件目に3枚", b.ev("regItems()[0].photoNames.length"), 3)
r.check("3件目は3枚", b.ev("regItems()[2].photoNames.length"), 3)

print("■ 出品用のタイトルはそのまま作れる")
t = b.ev("buildTitle(products[0], {})")
r.expect("タイトルに品種と管理番号", "幹之" in (t or "") and (b.ev("regItems()[0].controlNo") in (t or "")), t)

b.close(); r.finish()
