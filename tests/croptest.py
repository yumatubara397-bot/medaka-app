"""拡大のゲージと「この範囲で保存」を検証する。
   保存された画像の中身（切り取られているか）まで見る。"""
import time, base64, io
from common import Browser, Report
from PIL import Image

b = Browser(9360, 1300, 1100); r = Report()
b.ev("localStorage.clear();switchTab('register');renderRegisterPanel()"); time.sleep(0.8)
b.ev("""{ TepraLink._kind='none';
  regSel.breed=regMasters().breeds.find(x=>x.name==='幹之');
  regSel.rank='特上'; regSel.qtyMode='pair'; regSel.qtyN=1; regSel.step=3; regDoRegister(); }""")
time.sleep(1.0)
# 四隅と中央で色を変えた写真を作る（どこが切り取られたか分かるように）
b.ev("""(async()=>{ const cv=document.createElement('canvas'); cv.width=1000; cv.height=1000;
  const x=cv.getContext('2d');
  x.fillStyle='#ff0000'; x.fillRect(0,0,500,500);      // 左上 赤
  x.fillStyle='#00ff00'; x.fillRect(500,0,500,500);    // 右上 緑
  x.fillStyle='#0000ff'; x.fillRect(0,500,500,500);    // 左下 青
  x.fillStyle='#ffff00'; x.fillRect(500,500,500,500);  // 右下 黄
  x.fillStyle='#000000'; x.fillRect(400,400,200,200);  // 中央 黒
  const bl = await new Promise(res=>cv.toBlob(res,'image/jpeg',0.95));
  photos=[{name:'TEST.jpg', handle:{getFile:async()=>bl}, blobUrl:URL.createObjectURL(bl)}];
  folderHandle={name:'テスト'}; })()""")
time.sleep(1.2)
b.ev("switchTab('import');document.getElementById('assignPerItem').value=1;refreshAssignBar();assignPhotosToRegistered()")
time.sleep(1.2)
b.ev("document.querySelectorAll('#folderList .shot')[0].click()"); time.sleep(1.0)

print("■ ゲージ")
r.expect("ゲージがある", b.ev("!!document.getElementById('lbZoomRange')"), "")
r.check("開いたときの値", b.ev("document.getElementById('lbZoomRange').value"), "130")
r.check("％表示", b.ev("document.getElementById('lbZoomVal').textContent"), "130%")

b.ev("""{ const el=document.getElementById('lbZoomRange'); el.value='300';
   el.dispatchEvent(new Event('input',{bubbles:true})); }""")
time.sleep(0.6)
r.expect("ゲージで倍率が変わる", abs((b.ev("lbState.zoom") or 0) - 3.0) < 0.01, str(b.ev("lbState.zoom")))
r.check("％表示も変わる", b.ev("document.getElementById('lbZoomVal').textContent"), "300%")

b.ev("document.getElementById('lbZoomOut').click()"); time.sleep(0.5)
r.expect("ボタンで縮小するとゲージも動く",
         b.ev("document.getElementById('lbZoomRange').value") != "300",
         b.ev("document.getElementById('lbZoomRange').value"))

print("■ 中央を拡大して保存する")
b.ev("""{ const el=document.getElementById('lbZoomRange'); el.value='300';
   el.dispatchEvent(new Event('input',{bubbles:true})); }""")
time.sleep(0.8)
# 枠の中央にスクロールを合わせる（真ん中の黒が見えている状態にする）
b.ev("""{ const st=document.getElementById('lbStage');
   st.scrollLeft=(st.scrollWidth-st.clientWidth)/2;
   st.scrollTop=(st.scrollHeight-st.clientHeight)/2; }""")
time.sleep(0.5)
rect = b.ev("JSON.stringify(lbVisibleRect())")
r.expect("見えている範囲が元画像より小さい",
         (lambda d: d and d["w"] < 1000 and d["h"] < 1000)(__import__("json").loads(rect or "null")), rect)

b.ev("document.getElementById('lbSaveCrop').click()"); time.sleep(2.5)
r.expect("保存された", b.ev("!!(editState[0] && editState[0].editedBlobUrl)"), str(b.ev("editState[0] && editState[0].modes")))
r.check("切り取りとして記録", b.ev("editState[0].modes"), ["crop"])

# 保存された画像を取り出して中身を見る
data = b.ev("""(async()=>{ const res=await fetch(editState[0].editedBlobUrl); const bl=await res.blob();
  return await new Promise(r=>{const fr=new FileReader();fr.onload=()=>r(fr.result.split(',')[1]);fr.readAsDataURL(bl);}); })()""")
if data:
    im = Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB")
    r.expect("縦横とも切り取られている", im.width < 1000 and im.height < 1000, f"{im.width}×{im.height}")
    cx, cy = im.width // 2, im.height // 2
    px = im.getpixel((cx, cy))
    r.expect("中央は黒（真ん中を切り取れている）", sum(px) < 150, str(px))
    corner = im.getpixel((2, 2))
    r.expect("端は黒ではない（四隅の色が残る）", sum(corner) > 100, str(corner))

print("■ 保存したものが出品に使われる")
b.ev("switchTab('listing');renderListingPanel()"); time.sleep(0.8)
plan = b.ev("JSON.stringify(planImages(products[0]))")
r.expect("加工後として扱われる", '"edited":true' in (plan or ""), plan)

print("■ 比較表示のときは保存しない")
b.ev("openLightbox(0,'after'); lbState.compareMode=true;"); time.sleep(0.6)
b.ev("window.__t=''; const _t=toast; toast=(m,k)=>{window.__t=m; return _t(m,k);};")
b.ev("lbSaveCrop()"); time.sleep(0.8)
r.expect("断って理由を出す", "比較表示" in (b.ev("window.__t") or ""), b.ev("window.__t"))

b.close(); r.finish()
