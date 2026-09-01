"""用品の固定写真と固定の管理番号を検証する。"""
import time, datetime
from common import Browser, Report

b = Browser(9364, 1200, 1300); r = Report()
today = datetime.date.today().strftime("%y%m%d")
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(1.0)
b.ev("window.confirm = () => true; TepraLink._kind='none'")

print("■ 固定の管理番号が振られている")
nos = b.ev("regMasters().goods.map(g=>g.fixedNo)")
r.check("23件すべてに番号", len([n for n in (nos or []) if n]), 23)
r.check("重複なし", len(set(nos or [])), 23)
r.expect("YO-01 から始まる", (nos or [])[0] == "YO-01", str((nos or [])[:3]))

print("■ 用品を登録すると固定番号が使われる")
b.ev("regSel.mode='goods'; regSel.step=1; renderRegisterPanel()"); time.sleep(0.8)
b.ev("[...document.querySelectorAll('#regBreedList button')].find(x=>x.querySelector('.bn').textContent==='ホテイソウ').click()")
time.sleep(0.8)
hotei_no = b.ev("goodsOf('ホテイソウ').fixedNo")
r.expect("番号が出ている", bool(hotei_no), str(hotei_no))
b.ev("[...document.querySelectorAll('#wheelQty .wheel-item')].find(e=>e.textContent==='5').click()"); time.sleep(0.6)
b.ev("document.getElementById('regStep2Next').click()"); time.sleep(0.6)
r.expect("確認に固定番号が出る", hotei_no in (b.ev("document.getElementById('regStepBody').textContent") or ""),
         (b.ev("document.getElementById('regStepBody').textContent") or "").replace("\n"," ")[:90])
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(0.8)
r.check("管理番号は固定のもの", b.ev("regItems()[0].controlNo"), hotei_no)
r.check("1件だけ", b.ev("regItems().length"), 1)

print("■ 同じ用品をもう一度登録しても増えない（数量が書き替わる）")
b.ev("regSel.mode='goods'; regSel.step=1; renderRegisterPanel()"); time.sleep(0.6)
b.ev("[...document.querySelectorAll('#regBreedList button')].find(x=>x.querySelector('.bn').textContent==='ホテイソウ').click()")
time.sleep(0.8)
b.ev("[...document.querySelectorAll('#wheelQty .wheel-item')].find(e=>e.textContent==='12').click()"); time.sleep(0.6)
b.ev("document.getElementById('regStep2Next').click()"); time.sleep(0.5)
b.ev("document.getElementById('regDoRegister').click()"); time.sleep(0.8)
r.check("やはり1件", b.ev("regItems().length"), 1)
r.check("数量だけ変わる", b.ev("regItems()[0].quantityText"), "12個")
r.check("番号は同じ", b.ev("regItems()[0].controlNo"), hotei_no)

print("■ 魚の通し番号は用品に食われない")
b.ev("""{ regSel.mode='fish'; regSel.breed=regMasters().breeds.find(x=>x.name==='幹之');
  regSel.rank='特上'; regSel.qtyMode='pair'; regSel.qtyN=1; regSel.step=3; regDoRegister(); }""")
time.sleep(0.8)
fish = [x for x in b.ev("regItems().map(x=>({no:x.controlNo,kind:x.kind}))") if x["kind"] != "goods"]
r.check("魚は001から", fish[0]["no"], f"MD-{today}-001")

print("■ 固定写真を登録する")
b.ev("""(async()=>{ const mk=(c)=>{const cv=document.createElement('canvas');cv.width=cv.height=300;
   const x=cv.getContext('2d');x.fillStyle=c;x.fillRect(0,0,300,300);
   return new Promise(res=>cv.toBlob(res,'image/jpeg',0.9)); };
  const b1=await mk('#2b6cb0'), b2=await mk('#2f855a');
  window.__f1=new File([b1],'p1.jpg',{type:'image/jpeg'});
  window.__f2=new File([b2],'p2.jpg',{type:'image/jpeg'}); })()""")
time.sleep(1.0)
b.ev("goodsAddPhotos('ホテイソウ',[window.__f1,window.__f2])"); time.sleep(1.5)
r.check("2枚が登録される", len(b.ev("goodsPhotoKeys('ホテイソウ')") or []), 2)
r.expect("中身も取り出せる", b.ev("(async()=>{const bl=await goodsPhotoGet(goodsPhotoKeys('ホテイソウ')[0]); return !!(bl&&bl.size);})()"),
         "IndexedDBに入っている")

print("■ 画面にも並ぶ")
b.ev("regSel.mode='goods'; regSel.step=1; renderRegisterPanel()"); time.sleep(0.6)
b.ev("[...document.querySelectorAll('#regBreedList button')].find(x=>x.querySelector('.bn').textContent==='ホテイソウ').click()")
time.sleep(1.2)
r.check("2枚並ぶ", b.ev("document.querySelectorAll('#goodsPhotos .gp').length"), 2)
r.expect("写真が読み込まれる", b.ev("[...document.querySelectorAll('#goodsPhotos img')].every(i=>i.src.startsWith('blob:'))"), "")
r.expect("追加ボタンがある", b.ev("!!document.getElementById('goodsPhotoAdd')"), "")

print("■ 取込で、用品は撮った写真を使わず固定写真が入る")
b.ev("""(async()=>{ const mk=(c)=>{const cv=document.createElement('canvas');cv.width=400;cv.height=300;
   const x=cv.getContext('2d');x.fillStyle=c;x.fillRect(0,0,400,300);
   return new Promise(res=>cv.toBlob(res,'image/jpeg',0.9)); };
  photos=[]; for(const c of ['#b7791f','#9b2c2c','#553c9a']){ const bl=await mk(c);
    photos.push({name:'FISH_'+photos.length+'.jpg', handle:{getFile:async()=>bl}, blobUrl:URL.createObjectURL(bl)}); }
  folderHandle={name:'テスト'}; })()""")
time.sleep(1.2)
b.ev("switchTab('import');document.getElementById('assignPerItem').value=3;refreshAssignBar();assignPhotosToRegistered()")
time.sleep(2.0)
r.check("商品は2件（用品＋魚）", b.ev("products.length"), 2)
goods_p = b.ev("JSON.stringify(products.find(p=>p.controlNo.startsWith('YO-')))")
r.expect("用品に固定写真2枚がつく",
         b.ev("products.find(p=>p.controlNo.startsWith('YO-')).specimenIdxs.length") == 2, goods_p[:120])
r.check("魚には撮った3枚",
        b.ev("products.find(p=>p.controlNo.startsWith('MD-')).specimenIdxs.length"), 3)
r.expect("用品の写真名は管理番号から作る",
         (b.ev("products.find(p=>p.controlNo.startsWith('YO-')).specimenIdxs.map(i=>photos[i].name)") or [""])[0].startswith("YO-"),
         str(b.ev("products.find(p=>p.controlNo.startsWith('YO-')).specimenIdxs.map(i=>photos[i].name)")))
r.expect("撮った写真は魚だけに使われる",
         b.ev("products.find(p=>p.controlNo.startsWith('MD-')).specimenIdxs.map(i=>photos[i].name).every(n=>n.startsWith('FISH_'))"),
         str(b.ev("products.find(p=>p.controlNo.startsWith('MD-')).specimenIdxs.map(i=>photos[i].name)")))

print("■ 管理番号は変えられる")
b.ev("switchTab('register')")
r.check("重なる番号は断る", b.ev("setGoodsNumber('ホテイソウ', goodsOf('ラムズホーン').fixedNo).ok"), False)
b.ev("setGoodsNumber('ホテイソウ','YOHIN-001')"); time.sleep(0.5)
r.check("変えられる", b.ev("goodsOf('ホテイソウ').fixedNo"), "YOHIN-001")
r.check("登録ずみのぶんも付け替わる",
        b.ev("regItems().find(x=>x.kind==='goods').controlNo"), "YOHIN-001")

print("■ 固定写真は消せる")
b.ev("goodsRemovePhoto('ホテイソウ', goodsPhotoKeys('ホテイソウ')[0])"); time.sleep(0.8)
r.check("1枚に減る", len(b.ev("goodsPhotoKeys('ホテイソウ')") or []), 1)

b.close(); r.finish()
